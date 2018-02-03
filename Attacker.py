import hlt
import logging
from collections import OrderedDict
import math


# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Attacker")
# Then we print our start message to the logs
logging.info("Starting my Attacker bot!")

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
        if i == 0 or i == 1:
            continue
        
        ship = [s for s in game_map.get_me().all_ships() if s.id == ship_ids[i]][0]
        
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
        
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id and entities_by_distance[distance][0].docking_status == entities_by_distance[distance][0].DockingStatus.UNDOCKED]
        
        closest_enemy = closest_enemy_ships[0]
        
        bad_guys = [sh for sh in closest_enemy_ships if ship.calculate_distance_between(sh) < 13]
        
        if bad_guys:
            damage = len(bad_guys) * 64
            if (ship.health - damage) < 1:
                logging.info("My health is " + str(ship.health) + " and I'm gonna die")
                logging.info("I'm gonna ram him!!")
                navigate_command = ship.navigate(
                    Position(closest_enemy.x, closest_enemy.y),
                    game_map,
                    speed=hlt.constants.MAX_SPEED,
                    avoid_obstacles=True,
                    max_corrections=90,
                    angular_step=1,
                    ignore_ships=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                    continue
            
        move_towards(ship, closest_enemy)
        
        logging.info("My name is " + str(ship.id) + " and my health is " + str(ship.health))
        logging.info("The distance to the enemy is " + str(ship.calculate_distance_between(closest_enemy)))
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
