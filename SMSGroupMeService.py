# Author: Keith E. Kelly - 1/12/2019
import threading
import requests
import time
from SMSCommands import SMSCommands

class SMSTextMessage(object):
    id = None
    name = None
    text = None
    commands = None

class SMSGroupMember(object):
    id = None
    name = None
    phone_number = None

    def __init__(self, name, phone_number):
        self.name = name
        self.phone_number = phone_number

class SMSGroupMeService(threading.Thread):
    
    BASE_URL = "https://api.groupme.com/v3"
    
    _gh = None
    _access_token = ""
    _group_id = ""
    _bot_id = ""
    _last_scanned_message_id = None

    bot_name = ""
    commands = None
    members = None
    last_message = None
    command_list = None
 
    def __init__(self, access_token, greenhouse_service, bot_name = "gh"):
        threading.Thread.__init__(self)
        
        self._access_token = access_token
        self.ghs = greenhouse_service
        self._group_name = "%s_%s" % ("iot_gh", self.ghs.greenhouse.group_id)
        self.bot_name = "%s%s" % ("gh",self.ghs.greenhouse.house_number)
        
        commands = SMSCommands()
        self.members = {}

        self._group_id = self._get_group_id()
        if self._group_id == None:
            self._group_id = self._make_group()
        self._bot_id = self._get_bot_id()
        if self._bot_id == None:
            self._bot_id = self._make_bot()
        #self._send_intro_message()
        #self._last_scanned_message_id = self._get_last_scanned_message_id()
        
        self.daemon = True
        self.start()

    def run(self):
        while True:
            next_commands = self._get_next_commands()
            if next_commands != None:
                self._execute_commands(next_commands)
            time.sleep(2)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for member in self.members:
            self._remove_member(member)
        
    def _get_group_id(self):
        group_id = None
        params = {"token": self._access_token}
        headers = {"content-type": "application/json"}
        end_point = "/groups"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch group. Please verify your access token." + r.text)
        else:
            groups = r.json()["response"]
            for group in groups:
                if group["name"] == self._group_name:
                    group_id = group["id"]
                    group_phone_number = group["phone_number"]
                    break
        return group_id
    
    def _make_group(self):
        group_id = None
        params = {"token": self._access_token}
        payload = {"name": self._group_name} 
        headers = {"content-type": "application/json"}
        end_point = "/groups"
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.post(url, headers=headers, params=params, json=payload)
        if r.status_code != 201:
            raise Exception("Bad request. Unable to create group. " + r.text)
        else:
            group = r.json()["response"]
            group_id = group["id"]
        return group_id

    def _get_bot_id(self):
        bot_id = None
        #payload = {"group_id": self._group_id}
        headers = {"content-type": "application/json"}
        end_point = "bots"
        url = "%s/%s?token=%s" % (self.BASE_URL, end_point, self._access_token)
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        else:
            bots = r.json()["response"]
            for bot in bots:
                if bot["name"] == self.bot_name and bot["group_id"] == self._group_id:
                    bot_id = bot["bot_id"]
                    break
        return bot_id

    def _make_bot(self):
        bot_id = None
        payload = {"bot": {"name": self.bot_name, "group_id": self._group_id}} 
        headers = {"content-type": "application/json"}
        #url = self.BASE_URL + "/bots?token=" + self._access_token
        end_point = "bots"
        url = "%s/%s?token=%s" % (self.BASE_URL, end_point, self._access_token)
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code != 201:
            raise Exception("Bad request. Unable to create bot. " + r.text)
        else:
            bot = r.json()["response"]["bot"]
            bot_id = bot["bot_id"]
        return bot_id

    def _get_member_id(self, member_key):
        headers = {"content-type": "application/json"}
        end_point = "members/results/:"
        url = "%s/%s%s" % (self.BASE_URL, end_point, member_key)
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        else:
            members = r.json()["response"]
            #should be only one
            for member in members:
                member_id = member["id"]
                   
        return member_id
    
    def _remove_member(self, member_id):
        params = {"token": self._access_token}
        params["limit"] = 1 
        headers = {"content-type": "application/json"}
        end_point = "groups/%s/members/%s/remove" % self._group_id, member_id
        url = "%s/%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Bad request. Unable to fetch bot id. " + r.text)
        

    def add_member(self, phone_number):
        if phone_number not in self.members:
            user_name = "User%d" % (len(self.members) + 1)
            member = SMSGroupMember(user_name, phone_number)
            self.members[phone_number] = member
            params = {"token": self._access_token}
            params["limit"] = 1  
            payload = {"members": [{"nickname": member.name, "phone_number": member.phone_number, "guid": "guid_1"}]} 
            headers = {"content-type": "application/json"}
            end_point = "/groups/%s/members/add" % self._group_id
            url = "%s%s" % (self.BASE_URL, end_point)
            r = requests.post(url, headers=headers, params=params, json=payload)
            if r.status_code != 202:
                raise Exception("Bad request. Unable to create member request. " + r.text)
        

    
    def _send_message(self, message):
        payload = {"bot_id": self._bot_id, "text": message}
        headers = {"content-type": "application/json"}
        end_point = "bots/post"
        url = "%s/%s?token=%s" % (self.BASE_URL, end_point, self._access_token)
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code != 202:
            raise Exception("Unable to post message. " + r.text)
        else:
            self.last_message = SMSTextMessage()
            self.last_message.id = str(time.time())
            self.last_message.name = "gh"
            self.last_message.text = message
        
    #def _send_intro_message(self):
    #    m = "Hello. Send me a direct message (@gh) with the text '#help' for a list of IoT Greenhouse text commands. Use '#help-verbose' for detailed help text."
    #    self._send_message(m)

    
    def _get_last_scanned_message_id(self):
        last_message_id = None
        params = {"token": self._access_token}
        params["limit"] = 1  
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/messages" % self._group_id
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Unable to fetch messages. " + r.text)
        else:
            messages= r.json()["response"]["messages"]
            if len(messages) > 0:
                last_message_id = messages[0]["id"]
            else:
                raise Exception("No last message fount. " + r.text)

        return last_message_id
    
    def _get_next_commands(self):
        commands = None
        params = {"token": self._access_token}
        params["after_id"] = self._last_scanned_message_id  
        headers = {"content-type": "application/json"}
        end_point = "/groups/%s/messages" % self._group_id
        url = "%s%s" % (self.BASE_URL, end_point)
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise Exception("Unable to fetch messages. " + r.text)
        else:
            messages= r.json()["response"]["messages"]
            count = len(messages)
            if count > 0:
                self._last_scanned_message_id = messages[count-1]["id"]
                for message in messages:
                    if message["text"][:3] == "@gh":
                        self._last_scanned_message_id = message["id"]
                        self.last_message = SMSTextMessage()
                        self.last_message.id = message["id"]
                        self.last_message.name = message["name"]
                        self.last_message.text = message["text"]
                        s = message["text"].split()
                        if len(s) > 1:
                            s.pop(0)
                            commands = s
                            break
                        else:
                            time.sleep(1)
                            self._send_message("Sorry. I'd like to chat, but I'm only configured to response to valid IoT Greenhouse commands. Use '#help' or '#help_verbose' to see a list of valid commands.")
                
        return commands

    def _execute_commands(self, commands):
        cmds = [command.lower() for command in commands]
        cmds = [command.strip() for command in commands]
        if self._valid_commands(cmds):
            for cmd in cmds:
                m = self.command_list[cmd][2]
                if  m != "None":
                    self._send_message(m)
                c = self.command_list[cmd][0]
                if  c != "None":
                    try:
                        exec("self.%s" % c)
                    except:
                        self._send_message("Error: Invalid IoT Greenhouse command defined in command configuration file. %s" % c)
 
    def _valid_commands(self, commands):
        valid = True
        valid_commands = [self.command_list]
        for command in commands:
            if command not in self.command_list:
                self._send_message("Sorry. I'd like to chat, but I'm only configured to response to valid IoT Greenhouse commands. Use '#help' or '#help_verbose' to see a list of valid commands.")
                valid = False                
                break
        return valid

    def _load_command_file(self, filename):
        """Reads commands from CSV file
        """
        try:
            with open(filename) as csvfile:
                cmd_reader = csv.reader(csvfile, delimiter=',')
                self.command_list = {}
                for cmd in cmd_reader:
                    self.command_list[cmd[0]] = [cmd[1], cmd[2], cmd[3]] 

        except Exception as e:
            raise Exception("Unable to load commands. %s" % str(e))

    def send_command_list(self):
         m = "Valid IoT Greenhouse commands are: %s" % " ".join(self.command_list.keys() )
         self._send_message(m)

    def send_command_details(self):
        str_list = []
        str_list.append("Valid IoT Greenhouse commands are:\n\n")
        for cmd in self.command_list:
            s = "%s  %s\n" % (cmd, self.command_list[cmd][1])
            str_list.append(s)
  
        m =  "".join(str_list)
        self._send_message(m)

    def send_temperature(self):   
        temp = self.ghs.temperature.get_inside_temp_F()
        m = "Current greenhouse temperature is %s." % temp
        self._send_message(m)         

if __name__ == "__main__":
    
    
    from iot_gh.IoTGreenhouseService import IoTGreenhouseService
    ghs = IoTGreenhouseService()
    
    ACCESS_TOKEN = "oFmQLatuNvRR7Kpzs2wcp009r4MFHDSXZHOUG8o8"
    t_service = GHTextingService(ACCESS_TOKEN, ghs)

    last_message_id = None;
    while True:
        if t_service.last_message != None:
            if t_service.last_message.id != last_message_id:
                name = t_service.last_message.name
                text = t_service.last_message.text
                print(name + "   " + text)
                print()

                last_message_id = t_service.last_message.id
            time.sleep(1)
                


