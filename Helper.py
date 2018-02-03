import hlt
import logging
from collections import OrderedDict
import math

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Helper")
# Then we print our start message to the logs
logging.info("Starting my Helper bot!")

def move_towards(ship, entity):
    navigate_command = ship.navigate(
                ship.closest_point_to(entity),
                game_map,
                speed=3,
                avoid_obstacles=True,
                max_corrections=90,
                angular_step=1,
                ignore_ships=False)
    if navigate_command:
        command_queue.append(navigate_command)
        return True
    else:
        return False

turn = 0

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    
    turn += 1
    
    logging.info("It's turn " + str(turn))
    
    ship_ids = [ship.id for ship in game_map.get_me().all_ships()]
    
    for i in range(len(ship_ids)):
        if i == 0:
            continue
        
        ship = [s for s in game_map.get_me().all_ships() if s.id == ship_ids[i]][0]
        
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
        
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id and entities_by_distance[distance][0].docking_status == entities_by_distance[distance][0].DockingStatus.UNDOCKED]
        
        closest_enemy = closest_enemy_ships[0]

        move_towards(ship, closest_enemy)
        
        logging.info("My name is " + str(ship.id) + " and my health is " + str(ship.health))
        logging.info("The distance to the enemy is " + str(ship.calculate_distance_between(closest_enemy)))
    game.send_command_queue(command_queue)
    
    all_my_ships_list = game_map.get_me().all_ships()
    for ship in all_my_ships_list:
        logging.info(ship)
        logging.info(" and my health is " + str(ship.health))
    # TURN END
# GAME END
