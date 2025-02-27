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
    "spell_fields": [dictionary with simple key:value pairs from user input]
}

option = 0: quit the microservice
option = 1: Create a Spell -> Generate a JSON from given dictionary "spell_fields"
option = 2: Edit an existing Spell -> Change JSON fields in json_object based on "spell_fields"

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

def createDictFromArray(string_array):
    # Create a basic dictionary with all keys set to None
    spell_dict = {key: None for key in string_array}
    
    # Create the proper nested structure for complex fields
    if 'damage' in spell_dict:
        spell_dict['damage'] = {
            'damage_type': {'name': None},
            'damage_at_slot_level': {},
            'damage_at_character_level': {}
        }

    if 'school' in spell_dict:
        spell_dict['school'] = {'name': None}
    
    if 'classes' in spell_dict:
        spell_dict['classes'] = []
    
    if 'subclasses' in spell_dict:
        spell_dict['subclasses'] = []
    
    # Initialize as False for boolean fields
    if 'concentration' in spell_dict:
        spell_dict['concentration'] = False
    
    if 'ritual' in spell_dict:
        spell_dict['ritual'] = False
    
    # Initialize as empty lists for array fields
    if 'desc' in spell_dict:
        spell_dict['desc'] = ['']
    
    if 'higher_level' in spell_dict:
        spell_dict['higher_level'] = []
    
    if 'components' in spell_dict:
        spell_dict['components'] = []
    
    return spell_dict

# Function to parse user input fields into proper spell structure
def parseSpellFields(fields):
    # Start with the basic structure
    spell_dict = createDictFromArray(SECOND_LEVEL_PARAMS)
    
    # Fill in basic fields
    for key in ['name', 'level', 'range', 'casting_time', 'duration', 'attack_type']:
        if key in fields:
            spell_dict[key] = fields[key]
    
    # Set index and URL
    if 'name' in fields:
        spell_dict['index'] = fields['name'].lower().replace(" ", "-")
        spell_dict['url'] = "customized"
    
    # Handle description
    if 'desc' in fields:
        spell_dict['desc'] = [fields['desc']]
    
    # Handle higher level effects
    if 'higher_level' in fields and fields['higher_level']:
        spell_dict['higher_level'] = [fields['higher_level']]
    
    # Handle concentration
    if 'concentration' in fields:
        spell_dict['concentration'] = (fields['concentration'] == 'yes')
    
    # Handle ritual
    if 'ritual' in fields:
        spell_dict['ritual'] = (fields['ritual'] == 'yes')
    
    # Handle components
    if 'components' in fields:
        spell_dict['components'] = [comp.strip() for comp in fields['components'].split(',')]
    
    # Handle damage
    if 'has_damage' in fields and fields['has_damage'] == 'yes':
        if 'damage_type' in fields:
            spell_dict['damage']['damage_type']['name'] = fields['damage_type']
        
        if 'scaling_type' in fields and 'damage_values' in fields:
            damage_values = json.loads(fields['damage_values'])
            
            if fields['scaling_type'] == 'slot':
                for level, damage in damage_values.items():
                    spell_dict['damage']['damage_at_slot_level'][level] = damage
            elif fields['scaling_type'] == 'character':
                for level, damage in damage_values.items():
                    spell_dict['damage']['damage_at_character_level'][level] = damage
    
    # Handle school
    if 'school' in fields:
        spell_dict['school']['name'] = fields['school']
    
    # Handle classes
    if 'classes' in fields:
        for class_name in fields['classes'].split(','):
            class_name = class_name.strip()
            if class_name:
                spell_dict['classes'].append({'name': class_name})
    
    return spell_dict

# Customize a Spell -> Generate a JSON from given input
def createNewSpell(bookmarks, spell_fields):
    # Parse the input fields into a properly structured spell
    new_spell = parseSpellFields(spell_fields)
    
    # Add the new spell to bookmarks
    bookmarks.append(new_spell)
    return bookmarks

# Edit an existing Spell -> Change JSON fields from given input
def editSpell(bookmarks, spell_fields, spell):
    # Find the spell to edit
    spell_index = None
    for i, entry in enumerate(bookmarks):
        if entry.get('index') == spell.get('index'):
            spell_index = i
            break
    
    if spell_index is not None:
        # Parse the input fields into a properly structured spell
        updated_spell = parseSpellFields(spell_fields)
        
        # Preserve the original index if not changed
        if updated_spell['name'].lower().replace(" ", "-") != spell.get('index'):
            updated_spell['index'] = spell.get('index')
        
        # Replace the old spell with the updated one
        bookmarks[spell_index] = updated_spell
    
    return bookmarks

def main():
    # set up ZeroMQ
    context = zmq.Context()
    socket = context.socket(zmq.REP)

    # Binds REP socket to tcp://localhost:5554
    socket.bind("tcp://localhost:5554")
    proceed = 1 # continue waiting for next request while option != 0
    while (proceed != 0):
        returnBookmarks = []
        print("Spell Modifications Service Listening...")
        request = socket.recv()
        print(f"Received request: {request}")

        # convert byte string message to json
        decoded = json.loads(request.decode('utf-8'))
        print(f"Decoded request: {decoded}")

        # check if option is 0-- if it is, quit the service
        proceed = convertInt(decoded, "option")
        if (proceed != 0):
            option = decoded['option']
            # do the appropriate operation
            if (option == 1):
                returnBookmarks = createNewSpell(decoded['json_array'], decoded['spell_fields'])
            elif (option == 2):
                returnBookmarks = editSpell(decoded['json_array'], decoded['spell_fields'], decoded['json_object'])

            # convert returnBookmarks to byte string
            jsonReturnString = json.dumps(returnBookmarks)
            returnByteString = jsonReturnString.encode('utf-8')
            print(f"Response: {returnByteString}")
            socket.send(returnByteString)
        else:
            print("Spell Modifications Microservice has ended.")
            socket.send_string("") # send back empty string

if __name__ == "__main__":
    main()