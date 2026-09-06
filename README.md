# Pokemon-x-y-AP
my implementation for pokemon x/y archipelago

# Player Installation Steps
Drop APWorld: Copy pokemon_x_and_y.apworld into %ProgramData%\Archipelago\custom_worlds\ or you should be able to just run it maybe

Put the Pokemon_y_connector/Pokemon_x_connector depend on your game in your Archipelago\data\lua\ folder, might not be necessary but to be safe

Generate Seed: Use Pokemon X and Y.yaml in the Players/ folder and run ArchipelagoGenerate.exe.

# Play:
Load Pokémon X or Y in BizHawk.

Run connector_pokemon_y.lua/Pokemon_x_connector, or whatever i called it, in Tools -> Lua Console.

Connect using ArchipelagoBizHawkClient.exe.



# Known/potential problems:

At the start you may not think it is working, i could not find how to detect any checks before the first youngster austin battle (trainer sanity) or one of the item ball pickups, all of the tutorial stuff i dont think can be messed with (with current knowledge)

Some items being put in the wrong pockets of bag, can lead to a problem where you have to many items in your first pocket, you would likely need to recieve every single item in the game for this to be a problem and it shouldnt mess with anything essential, but some items might go to the wrong bag, just tell me

likely some locations missing/done incorrectly, tell me if you find one you feel should be a check, right now it should be all field items, the lua console should print out [EVENT FLAG SET] Flag ID: 0x0XXX where those three Xs are something like 25E, when you are reporting a location include that, if there is multiple send me all of them, even if i am checking 10 things for what you want, its better than however many there could possible be

my anti vanilla item pick up is a little bit jank, tell me if you run into an issue with it, i expect it to be extra weird if you try to do an async or if you have to close the game and reconnect, but tell me anything you run into and i will look into it.
i imagine it might be weird if you have collection upon completion turned on for other games, might work just fine

Some checks that are unreasonable to do mightve slipped through into logic so tell me any you encounter

Game version i imagine shouldnt matter, i believe i have just been using the base US version of Y

Universal Tracker should work, report any problems with it i will try to fix them

If you do run into an issue tell me and i did implement a way to manually send items/locations so at least your run shouldnt be dead, will try to find the best way to share that, but you need all the item/location ids

Any bugs or anything you run into, feel free to dm me, i am more likely to see it than in the pokemon x/y chat, but probably put it in both so more people cann see the problem and solution

Bizhawk sometimes frezzes, you may disconnect temporarily from archipelago but should be fine, hopefully


# AI DISCLOSURE

I have said since i started this that i do not know how to code, so i have done research, dug in the ram, done what i do know how to do, but the code is almost exclusively written by ai in both the world and the connectors, i have tested that it works, and i have ran the tests provided by archipelago, and i am ready to keep working to solve any bugs that show up, if anybody ever wants to take this over so it is no longer ai coded, feel free, i only am using ai because i want to play this and nobody was anywhere near starting working on this, ever, except for when i did this, will shout out the people who provided help for me on where to look and what to try doing, as well as the people that provided useful info to further this project, can add your names if you want just reach out
