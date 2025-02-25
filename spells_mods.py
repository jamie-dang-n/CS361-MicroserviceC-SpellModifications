import json
import zmq

#CONSTANTS
FIRST_LEVEL_PARAMS = ['index', 'name', 'level', 'url']
SECOND_LEVEL_PARAMS = ['index', 'name', 'url', 'desc', 'higher_level', 'range', 'components', 'material', 'area_of_effect', 'ritual', 'duration', 'concentration', 'casting_time', 'level', 'attack_type', 'damage', 'school', 'classes', 'subclasses', 'url']

"""
LISTENS ON PORT 5554
Expected Input Format: jsonified dictionary  (let "" represent a null (empty) string)
input_dict = {
    "option": [value is 0, 1, or 2],
    "json_array": json_array,
    "json_object": json_object,
    "new_fields": [dictionary with key:value pairs]
}

option = 0: quit the microservice
option = 1: Customize a Spell -> Generate a JSON from given dictionary "new_fields"
option = 2: Edit an existing Spell -> Change JSON fields in json_object to those of given dictionary "new_fields"

"""
# convertInt is used to convert fields
# from the input dictionary (hasValidData and option)
# to an integer. if conversion fails, the int = -1
def convertInt(dict, field):
    returnInt = 0
    try:
        if (dict[field]):
            returnInt = int(dict[field])
    except ValueError:
        returnInt = -1
    return returnInt

# Customize a Spell -> Generate a JSON from given input

# Edit an existing Spell -> Change JSON fields from given input


def main():
    # set up ZeroMQ
    context = zmq.Context()
    socket = context.socket(zmq.REP)

    # Binds REP socket to tcp://localhost:5554
    socket.bind("tcp://localhost:5554")
    proceed = 1 # continue waiting for next request while option != 0
    while (proceed != 0):
        print("Spell Modifications Service Listening...")
        request = socket.recv()
        print(f"Received request: {request}")

        # convert byte string message to json
        decoded = json.loads(request.decode('utf-8'))
        print(f"Decoded request: {decoded}")

        # check if option is 0-- if it is, quit the service
        proceed = convertInt(decoded, "option")
        if (proceed != 0):
            returnArray = []
            option = decoded['option']
            # do the appropriate operation
            socket.send(b"a message")
            
            # convert returnArray to byte string
            # jsonReturnString = json.dumps(returnArray)
            # returnByteString = jsonReturnString.encode('utf-8')
            # print(f"Response: {returnByteString}")
            # socket.send(returnByteString)
        else:
            print("Bookmark Modifications Microservice has ended.")
            socket.send_string("") # send back empty string

if __name__ == "__main__":
    main()