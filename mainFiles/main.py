import asyncio
from longchain.core.dataclasses import Message, PathResult, Player
from longchain.core.path import Path
from longchain.core.quest import Quest
from longchain.impl.actionresolver.sequential import SequentialActionResolver
from longchain.impl.agentaction.arbitrary import ArbitraryAgentAction
from longchain.impl.agentaction.end import ChangePathAction, RemovePlayerAction
from longchain.impl.agentaction.message import MessageAgentAction
from longchain.impl.datastore.jsonfile import JsonFileDatastore
from longchain.impl.messager.slack import SlackMessager
from longchain.impl.actionresolver.llm import LlmTool, LlmToolParam, LlmToolResult, OpenAIActionResolver
from longchain.plugins.bag import bag_instance
import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import base64

if "ENVIRONMENT" not in os.environ or os.environ["ENVIRONMENT"] != "production":
    import dotenv
    dotenv.load_dotenv(override=True)

ENV_VARS_REQUIRED = ["ENVIRONMENT", "GRASS_SLACK_BOT_TOKEN", "GRASS_SLACK_APP_TOKEN", "HOME_CHANNEL_ID", "DATA_FILEPATH", "BOT_USER_ID", "OPENAI_API_KEY", "OPENAI_API_URL", "ADMINS", "BAG_APP_ID", "BAG_APP_KEY", "QUEST_OWNER_ID"]
if not all([var in os.environ for var in ENV_VARS_REQUIRED]):
    raise Exception(f"Missing the following environment variables: {', '.join([var for var in ENV_VARS_REQUIRED if not var in os.environ])}")

datastore = JsonFileDatastore(os.environ["DATA_FILEPATH"])

bag_instance.configure(int(os.environ["BAG_APP_ID"]), os.environ["BAG_APP_KEY"], os.environ["QUEST_OWNER_ID"])

def player_has_bone(player: Player):
    inventory = bag_instance.get_inventory(player.id)
    has_bone = False
    for item in inventory:
        if item.itemId == "Bone":
            has_bone = True
            break
    return has_bone

image_path = "/home/v205/grassQuest/mainFiles/userData/"
def player_posted_image(player: Player):
    #os.path.isfile(player.id + ".png")
    user_id = player.id
    print(os.path.isfile(image_path+ user_id + ".png"))
    print("IMAGE CHECK ABOVE")
    return os.path.isfile(image_path+ user_id + ".png")

def image_description(player:Player):
    client = OpenAI(
        api_key=os.environ.get("OPEN_AI_TOKEN"),
        base_url="https://jamsapi.hackclub.dev/openai",
    )
    print(client.base_url)
    # Getting the base64 string
    user_id = player.id
    if player_posted_image(player):
        base64_image = encode_image(image_path + user_id + ".png")
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe the image."},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                },
                },
            ],
            }
        ],
        max_tokens=85,
        )
        image_description = response.choices[0].message.content
        print(image_description)
        return image_description




# Function to encode the image
def encode_image(image):
  with open(image, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')





#system_prompt=lambda ctx: f'You are a game master for an RPG. The player is in a town square. They are helping Agent Stocking, a spy who\'s lost his lucky socks. The player needs to go to the apartment over the bakery where they must convince a dog, Agent Duke, to help them track a thief. Duke cannot speak, but can understand when people speak to him. The player has a small flag that was left by the thief. 
# {"""However, the player has a bone in their inventory, so Duke is distracted and not interested in the flag. The player cannot get rid of the bones by simply saying "I throw the bones away" or something similar. They must remove them from their actual inventory. Do not tell them this directly, let them figure it out by themselves. After you describe what happens in the scene, prompt the player by asking "What do you do now?" Do not provide any specific suggestions to the player when you do this. Make sure to call the appropriate tool if the player resolves this encounter, either by abandoning it or by convincing Duke to help. """ if player_has_bone(ctx.player) else ""}',

quest = Quest(
    name="Collect Grass",
    paths=[
        Path(
            id="welcome",
            starts_without_player_action=True,
            action_resolver=SequentialActionResolver(
                MessageAgentAction("A tall figure wearing a hat walks towards you,  \"Hello, I'm the farmer. Could you help me with something?\" ", name="Welcome", icon_url="https://example.com/icon.png"),
                ChangePathAction("farmer_initial") # ChangePathAction("stocking_initial")
            )
        ),
     
        Path(
            id="farmer_initial",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                system_prompt="You are a game master for an RPG. Right now the player is in front of a barn. A hat wearing farmer, Farmer Smallberry, has approached them.  Farmer Smallberry has cows,  but it is winter and they need more grass to feed the cows! Without them, their cows will starve. They need to convince the player to go find grass! Farmer Smallberry should first introduce themself, then ask the player for help.",
                name="Farmer Smallberry",
                agent_actions=[
                    
                    LlmTool(
                        name="farmer_agree",
                        description="Call this tool once the player agrees to help Farmer Smallberry.",
                        params=[],
                        available=lambda ctx: True,

                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("farmer-instructions", next_action="path")],
                            model_feedback="Farmer Smallberry has convinced the player to help."
                        )
                    ),
                    LlmTool(
                        name="farmer_disagree",
                        description="Call this tool if the player refuses multiple times to help Farmer Smallberry.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("welcome", next_action="path")],
                            model_feedback="The player has refused to help Farmer Smallberry."
                        )
                    )
                ],
                preload_messages=[{"role": "assistant", "content": "A tall figure wearing a hat walks towards you,  \"Hello, I'm the farmer. Could you help me with something?\""}] # give the model context on what's already happened
            )
        ),  
        Path(
            id="farmer-instructions",
            starts_without_player_action=True,
            action_resolver=SequentialActionResolver(
                MessageAgentAction("\"Alrighty!\n It's winter, so there is not much grass, and I'm running out of it to feed the cows. Head up that road with this cart and scythe and you'll see a field of grass, cut some and bring it back, thanks\" the farmer says \n What do you do now? ", name="Head to the field", icon_url="https://example.com/icon.png"),
                ChangePathAction("grass_image") # ChangePathAction("stocking_initial")
            )
        ),  
        #{"""However, the player has a bone in their inventory, so Duke is distracted and not interested in the flag. The player cannot get rid of the bones by simply saying "I throw the bones away" or something similar. They must remove them from their actual inventory. Do not tell them this directly, let them figure it out by themselves. After you describe what happens in the scene, prompt the player by asking "What do you do now?" Do not provide any specific suggestions to the player when you do this. Make sure to call the appropriate tool if the player resolves this encounter, either by abandoning it or by convincing Duke to help. """ if player_has_bone(ctx.player) else ""}',

         Path(
            id="hs",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                #system_prompt="You are a game master for an RPG. Right now the player is in a field of grass. The player is supposed to upload a PNG image of grass. ",
                system_prompt='',
                name="Farmer Smallberry",
                agent_actions=[
                    
                    LlmTool(
                        name="image_contains_grass",
                        description="Call this tool if the image has.",
                        params=[],
                        available=lambda ctx: True,

                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("farmer-instructions", next_action="path")],
                            model_feedback="Farmer Smallberry has convinced the player to help."
                        )
                    ),
                    LlmTool(
                        name="farmer_disagree",
                        description="Call this tool if the player refuses multiple times to help Farmer Smallberry.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("welcome", next_action="path")],
                            model_feedback="The player has refused to help Farmer Smallberry."
                        )
                    )
                ],
                preload_messages=[{"role": "assistant", "content": "A tall figure wearing a hat walks towards you,  \"Hello, I'm the farmer. Could you help me with something?\""}] # give the model context on what's already happened
            )
        ),  
        
        Path(
            id="grass_image",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                #",
                system_prompt=lambda ctx: f'You are a game master for an RPG. Right now the player is in a field of grass. The player is supposed to upload a PNG image of grass, as a favor to an art loving hobbit who let the player pass. If the image has grass, call the appropriate tool. If the image description  does not contain grass, or there is no image, tell the user to upload a PNG image of grass. {"Image Description: " + image_description(ctx.player) if player_posted_image(ctx.player) else "The player has not uploaded a PNG image yet. Tell them to upload a PNG image of grass."}',
                
                #system_prompt=lambda ctx: f'You are a game master for an RPG. Right now the player is in a field of grass. The player is supposed to upload a PNG image of grass, as a favor to an art loving hobbit who let the player pass. If the image has grass, call the appropriate tool. If the image does not contain grass, or there is no image, tell the user to upload a PNG image of grass. {"Image Description: " if player_posted_image(ctx.player) else "The player has not uploaded a PNG image yet. Tell them to upload a PNG image of grass."}',
                agent_actions=[
                    LlmTool(
                        name="image_contains_grass",
                        description="Call this tool once the player has uploaded a image that contains grass.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("completed", next_action="path")],
                            model_feedback="The user has uploaded a image that contains grass."
                        )
                    ),
                    
                    LlmTool(
                        name="player_abandons",
                        description="Call this tool if the player refuses to follow the instructions DO NOT CALL THIS IF THE PLAYER MIGHT POST THE IMAGE LATER",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("completed", next_action="path")],
                            model_feedback="The player has abandoned the quest."
                        )
                    )
                    
                ],
                preload_messages=[{"role": "assistant", "content": "The hobbit smiles, \"Well, now go and get the grass for the farmer, but don't forget my image! \" "}]
            )
        ),
        
        Path(
            starts_without_player_action=True,
            id="completed",
            action_resolver=SequentialActionResolver(
                MessageAgentAction(f"You have completed the quest! You can try again by pinging <@{os.environ['BOT_USER_ID']}> in <#{os.environ['HOME_CHANNEL_ID']}>.", name="Completed", icon_url="https://example.com/icon.png"),
                RemovePlayerAction()
            ),
        ),

    ],
    
    message_sender=SlackMessager(
        bot_token=os.environ["GRASS_SLACK_BOT_TOKEN"],
        app_token=os.environ["GRASS_SLACK_APP_TOKEN"],
        start_path="welcome",
        datastore=datastore,
        active_channel=os.environ["HOME_CHANNEL_ID"],
        reset_user_command="/grass-reset-user", # CHANGE THIS to something unique to your quest
        admins=os.environ["ADMINS"].split(',')
        ),
    datastore=datastore
)

asyncio.run(quest.run())




'''
        Path(
            id="farmer_initial",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                system_prompt="You are a game master for an RPG. Right now the player is in a town square. A cloaked figure, Agent Stocking, has approached them. Agent Stocking is a spy, but someone has stolen his lucky socks! Without them, he cannot be stealthy. He needs to convince the player to go find his socks! Agent Stocking should first introduce himself, then ask the player for help.",
                name="Cloaked Figure",
                agent_actions=[
                    LlmTool(
                        name="stocking_agree",
                        description="Call this tool once the player agrees to help Agent Stocking.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("stocking_agree_transistion", next_action="path")],
                            model_feedback="Agent Stocking has convinced the player to help."
                        )
                    ),
                    LlmTool(
                        name="stocking_disagree",
                        description="Call this tool if the player refuses multiple times to help Agent Stocking.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("completed", next_action="path")],
                            model_feedback="The player has refused to help Agent Stocking."
                        )
                    )
                ],
                preload_messages=[{"role": "assistant", "content": "A cloaked figure approaches you. They look like they're trying to be sneaky, but they're not doing a very good job of it. \"Hello, traveller,\" they whisper."}] # give the model context on what's already happened
            )
        ),
        Path(
            id="stocking_agree_transistion",
            starts_without_player_action=True,
            action_resolver=SequentialActionResolver(
                MessageAgentAction("Agent Stocking nods. \"Thank you, traveller. I will be waiting for you in the forest to the east.\" He presses a small green-and-yellow flag into your hands. \"This was left by the perpetrator. My friend, Agent Duke, may be able to help track them down. He lives above the bakery.\" You open your mouth to speak, but Agent Stocking is gone in a not-nearly-as-stealthy-as-it-could-have-been flash.\nWhat do you do?", name="Agree", icon_url="https://example.com/icon.png"),
                ChangePathAction("duke_convince")
            )
        ),
        Path(
            id="duke_convince",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                system_prompt=lambda ctx: f'You are a game master for an RPG. The player is in a town square. They are helping Agent Stocking, a spy who\'s lost his lucky socks. The player needs to go to the apartment over the bakery where they must convince a dog, Agent Duke, to help them track a thief. Duke cannot speak, but can understand when people speak to him. The player has a small flag that was left by the thief. {"""However, the player has a bone in their inventory, so Duke is distracted and not interested in the flag. The player cannot get rid of the bones by simply saying "I throw the bones away" or something similar. They must remove them from their actual inventory. Do not tell them this directly, let them figure it out by themselves. After you describe what happens in the scene, prompt the player by asking "What do you do now?" Do not provide any specific suggestions to the player when you do this. Make sure to call the appropriate tool if the player resolves this encounter, either by abandoning it or by convincing Duke to help. """ if player_has_bone(ctx.player) else ""}',
                agent_actions=[
                    LlmTool(
                        name="duke_agrees",
                        description="Call this tool once the player has convinced Agent Duke to help them.",
                        params=[],
                        available=lambda ctx: not player_has_bone(ctx.player),
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("duke_agrees_transition", next_action="path")],
                            model_feedback="Agent Duke has agreed to help the player."
                        )
                    ),
                    LlmTool(
                        name="player_abandons",
                        description="Call this tool if the player refuses to help Agent Duke and walks out of the apartment with no intent to return. DO NOT CALL THIS IF THE PLAYER MIGHT COME BACK TO THE APARTMENT LATER.",
                        params=[],
                        available=lambda ctx: True,
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("completed", next_action="path")],
                            model_feedback="The player has abandoned the quest."
                        )
                    )
                ],
                preload_messages=[{"role": "assistant", "content": "Agent Stocking nods. \"Thank you, traveller. I will be waiting for you in the forest to the east.\" He presses a small green-and-yellow flag into your hands. \"This was left by the perpetrator. My friend, Agent Duke, may be able to help track them down. He lives above the bakery.\" You open your mouth to speak, but Agent Stocking is gone in a not-nearly-as-stealthy-as-it-could-have-been flash."}]
            )
        ),
        Path(
            id='duke_agrees_transition',
            starts_without_player_action=True,
            action_resolver=SequentialActionResolver(
                MessageAgentAction("Agent Duke has agreed to help! Here's a placeholder for the rest of the quest."),
                ChangePathAction("completed", next_action="path")
            )
        ),
        Path(
            starts_without_player_action=True,
            id="completed",
            action_resolver=SequentialActionResolver(
                MessageAgentAction(f"You have completed the quest! You can try again by pinging <@{os.environ['BOT_USER_ID']}> in <#{os.environ['HOME_CHANNEL_ID']}>.", name="Completed", icon_url="https://example.com/icon.png"),
                RemovePlayerAction()
            )
        )
    ],
    '''

'''

       Path(
            id="head-to-grass",
            starts_without_player_action=False,
            action_resolver=SequentialActionResolver(
                MessageAgentAction("A hobbit walks from the side of the road, crosses their arms, and stops in front of you, \"What are you doing here? Who sent  you? Scram!\"", name="Hobbit", icon_url="https://example.com/icon.png"),
                ChangePathAction("hobbit_answer") # ChangePathAction("stocking_initial")
            ),
        ),  

        Path(
            id="hobbit_convince",
            starts_without_player_action=False,
            action_resolver=OpenAIActionResolver(
                openai_token=os.environ["OPENAI_API_KEY"],
                openai_base_url=os.environ["OPENAI_API_URL"],
                model="gpt-4o-mini",
                #{"""However, the player has a bone in their inventory, so Duke is distracted and not interested in the flag. The player cannot get rid of the bones by simply saying "I throw the bones away" or something similar. They must remove them from their actual inventory. Do not tell them this directly, let them figure it out by themselves. After you describe what happens in the scene, prompt the player by asking "What do you do now?" Do not provide any specific suggestions to the player when you do this. Make sure to call the appropriate tool if the player resolves this encounter, either by abandoning it or by convincing Duke to help. """ if player_has_bone(ctx.player) else ""}
                system_prompt=lambda ctx: f'You are a game master for an RPG. The player is on a road towards a field. They are helping Farmer Smallberry, a farmer who needs grass for cows. The player needs to go to the road to the field where they must convince a hobbit to let them pass.   ',
                agent_actions=[
                    LlmTool(
                        name="hobbit-pass",
                        description="Call this tool once the player has convinced Agent Duke to help them.",
                        params=[],
                        available=lambda ctx: not player_has_bone(ctx.player),
                        action=lambda ctx, params: LlmToolResult(
                            agent_actions=[ChangePathAction("hobbit-allows", next_action="path")],
                            model_feedback="The Hobbit has agreed to let the player pass."
                        )
                    ),

                ],
                preload_messages=[{"role": "assistant", "content": "Agent Stocking nods. \"Thank you, traveller. I will be waiting for you in the forest to the east.\" He presses a small green-and-yellow flag into your hands. \"This was left by the perpetrator. My friend, Agent Duke, may be able to help track them down. He lives above the bakery.\" You open your mouth to speak, but Agent Stocking is gone in a not-nearly-as-stealthy-as-it-could-have-been flash."}]
            )
        ),
'''