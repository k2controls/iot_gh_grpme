''' IoT Greenhouse - GroupMe SMS Service
    Keith E. Kelly
    K2 Creatives, LLC
'''
from time import sleep

#from iot_gh.IoTGreenhouseService import IoTGreenhouseService
from ghs_mock import ghs_mock as IoTGreenhouseService
from SMSGroupMeService import SMSGroupMeService

print("\nGroupMe SMS Texting for IoT Greenhouse.\n")
#Enter house name and GroupMe token when prompted.
#name = input("Enter a short name for your greenhouse: ")
#print("\nOpen your dev.groupme.com page. Access your token and copy here.")
#token = input("GroupMe token: ")
groupMe_token = "cW3Q3QTXjx8ZUJPLozNwrO0zINyFx5Dig42g9NZa"

last_message_id = None

ghs = IoTGreenhouseService()
with SMSGroupMeService(groupMe_token, ghs) as sms_service:
    new_phone = None
    print()
    print("Enter a mobile phone number to assign to the GroupMe service.")
    print("Multiple numbers can be added. Press Enter when done.")
    while new_phone != "":
        new_phone = input("Phone number: ").strip()
        if new_phone != "":
            sms_service.add_member(new_phone)

    member_count = len(sms_service.members)
    if member_count == 0:
        print("No members added. Unable to continue.")
        exit()       
    else:
        print("%i phone numbers have been added to this service.")
        print()
        print("Send direct messages to this greenhouse using %s" % sms_service.bot_name)
        print("Include a command using the hash (#) character.")
        print("Example: %s #temp" % sms_service.bot_name)
        print("For a list of commands enter:  %s #help" % sms_service.bot_name)
        print()

        while True:
            message = ts.last_message
            if message.id != last_message_id:
                print(message.name + "   " + message.text)
                print()

                last_message_id = message.id
            sleep(.5)
