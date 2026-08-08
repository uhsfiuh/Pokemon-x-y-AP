# Pokemon-x-y-AP
my implementation for pokemon x/y archipelago

# Player Installation Steps
Drop APWorld: Copy pokemon_x_and_y.apworld into %ProgramData%\Archipelago\custom_worlds\.

Generate Seed: Use Pokemon X and Y.yaml in the Players/ folder and run ArchipelagoGenerate.exe.

# Play:
Load Pokémon X or Y in BizHawk.

Run connector_pokemon_y.lua in Tools -> Lua Console.

Connect using ArchipelagoBizHawkClient.exe.



# Known/potential problems:

At the start you may not think it is working, i could not find how to detect any checks before the first youngster austin battle (trainer sanity) or one of the item ball pickups, all of the tutorial stuff i dont think can be messed with (with current knowledge)

Some items being put in the wrong pockets of bag, can lead to a problem where you have to many items in your first pocket, you would likely need to recieve every single item in the game for this to be a problem and it shouldnt mess with anything essential

likely some locations missing/done incorrectly, tell me if you find one you feel should be a check, right now it should be all field items

my anti vanilla item pick up is a little bit jank, tell me if you run into an issue with it, i expect it to be extra weird if you try to do an async or if you have to close the game and reconnect, but tell me anything you run into and i will look into it.
i imagine it might be weird if you have collection upon completion turned on for other games, might work just fine

Some checks that are unreasonable to do mightve slipped through into early logic so tell me any you encounter

Game version i imagine shouldnt matter, i believe i have just been using the base us version of Y
I have not tested with pokemon x at all

If you do run into an issue tell me and i did implement a way to manually send items/locations so at least your run shouldnt be dead, will try to find the best way to share that, but you need all the item/location ids
