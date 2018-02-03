import hlt
import logging
import math
import time
from collections import OrderedDict

# a function to try to avoid conflicts when two ships attempt to dock on the same planet at once
# goes through the command queue and if it finds two docking commands with the same target, it removes one
def avoid_dock_conflicts():
    while True:
        destination = None
        avoided_conflict = False
        for command in command_queue:
            if "d" in command:
                # logging.info("d in command " + str(command))
                params = command.split(" ")
                if destination:
                    #logging.info("destination is set as " + str(destination))
                    if destination == params[2]:
                        #logging.info("conflict detected")
                        command_queue.remove(command)
                        #logging.info(str(command_queue))
                        avoided_conflict = True
                        break
                else:
                    destination = params[2]
                    #logging.info("set destination as " + str(destination))
        if avoided_conflict == False:
            break
            
# returns true if the total time for calculations is 90% of the allowed 2 seconds
def out_of_time():
    t1 = time.time()
    if (t1-t0) > (.90 * 2):
        return True
    return False

# a helper method to have all ships navigating the same way
def move_towards(ship, entity):
    navigate_command = ship.navigate(
                ship.closest_point_to(entity),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                avoid_obstacles=True,
                max_corrections=MAX_CORRECTIONS_SLIDER,
                angular_step=ANGULAR_STEP_SLIDER,
                ignore_ships=False)
    if navigate_command:
        command_queue.append(navigate_command)
        return True
    else:
        return False
    # else, skip turn
    

# GAME START
game = hlt.Game("AngryWasp")
logging.info("Starting my AngryWasp bot!")

turn = 0

harasser_list = []

while True:
    t0 = time.time()
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    
    turn += 1
    
    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    
    all_my_ships_list = game_map.get_me().all_ships()
    
    number_of_total_ships = len(all_my_ships_list)
    
    # at the beginning of the game, corrections can be near 90 and the angular step can be low
    # as ships approach and exceed 80, corrections are reduced to 18 (min) and angular step to 5 (max)
    #   to cut down on calculation time
    MAX_CORRECTIONS_SLIDER = 90 - (number_of_total_ships - 3)
    if MAX_CORRECTIONS_SLIDER < 18:
        MAX_CORRECTIONS_SLIDER = 18
    ANGULAR_STEP_SLIDER = int((4/77 * number_of_total_ships + 1))
    if ANGULAR_STEP_SLIDER > 5:
        ANGULAR_STEP_SLIDER = 5
    
    # Get a list of all ships that aren't docked 
    ships_to_move = [ship for ship in game_map.get_me().all_ships() if ship.docking_status == ship.DockingStatus.UNDOCKED]
    ships_moved = []
    
    # get list of all the planets that are not owned or are owned by me, but not full
    unowned_planets_or_dockable_I_own = [planet for planet in game_map.all_planets() if planet.is_owned() == False or (planet.owner.id == game_map.get_me().id and len(planet.all_docked_ships()) != planet.num_docking_spots)]
    
    # dictionary of planets matched to max ships targeting
    planet_targets_dict = {planet:(planet.num_docking_spots - len(planet.all_docked_ships())) for planet in unowned_planets_or_dockable_I_own}
    
    if turn == 1:
        # on the first turn, always make the first ship a harasser
        harasser_list.append(ships_to_move[0].id)
        all_my_ships_id_list = [ship.id for ship in all_my_ships_list]
        unit_number = len(all_my_ships_id_list)
    else:
        new_ship_ids = [ship.id for ship in all_my_ships_list if ship.id not in all_my_ships_id_list]
        
        for id in new_ship_ids:
            unit_number += 1
            if unit_number % 5 == 0:
                harasser_list.append(id)
            all_my_ships_id_list.append(id)
    
    for ship in ships_to_move:
        if out_of_time():
            break
            
        # harasser logic
        if ship.id in harasser_list:
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
        
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id and entities_by_distance[distance][0].docking_status != entities_by_distance[distance][0].DockingStatus.UNDOCKED]
            
            # send harassers to nearest docked ship
            if closest_enemy_ships:
                
                closest_enemy = closest_enemy_ships[0]
                #logging.info("harasser " + str(ship.id) + " closest enemy is docked")
            else:
                closest_enemy = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id][0]
                #logging.info("harasser " + str(ship.id) + " closest enemy is undocked")

            if move_towards(ship, closest_enemy):
                ships_moved.append(ship)
                continue
            else:
                continue
        
        # normal ships
        # if there are no more planet destinations, break
        if len(planet_targets_dict.keys()) == 0:
            break
        
        # get list of nearest planets to this ship
        nearest_planets = sorted(list(planet_targets_dict.keys()), key=ship.calculate_distance_between)
        
        nearest_planet = nearest_planets[0]
        
        # If the ship can dock, dock do it
        if ship.can_dock(nearest_planet):
            command_queue.append(ship.dock(nearest_planet))
        else:
            # move toward nearest planet
            if move_towards(ship, nearest_planet) == False:
                continue
                
        # ship has either docked or navigated toward the nearest planet
        # decrement planet targeters and clean dict, if necessary
        planet_targets_dict[nearest_planet] -= 1
        
        # if no more ships can head there, remove it from the viable planet list
        if planet_targets_dict[nearest_planet] == 0:
            planet_targets_dict.pop(nearest_planet, None)
            

        ships_moved.append(ship)
        #logging.info("appended ship " + str(ship.id) + " to moved list")
        
        #logging.info("length of ships_to_move is " + str(len(ships_moved)))
        
    # take moved ships out of "to move" list
    for ship in ships_moved:
        ships_to_move.remove(ship)

    if ships_to_move:
        # move remaining ships to attack docked ships on nearest center of available armada
        #logging.info("ships left to move:\n" + str(ships_to_move))
        
        # get center of armada
        _x = [ship.x for ship in ships_to_move]
        _y = [ship.y for ship in ships_to_move]
        _len = len(ships_to_move)
        #logging.info("x is " + str(_x) + "y is " + str(_y) + "len is " + str(_len))
        center_of_armada = {}
        center_of_armada_x = sum(_x)/_len
        center_of_armada_y = sum(_y)/_len
        
        #logging.info("got center of armada...")
        
        # send all remaining ships to planet nearest the center
        enemy_planets = sorted([planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id != game_map.get_me().id], key=lambda p: math.sqrt((center_of_armada_x - p.x) ** 2 + (center_of_armada_y - p.y) ** 2))
        
        if enemy_planets:
            target_enemy_ships = enemy_planets[0].all_docked_ships()
        
            #logging.info(str(target_enemy_ships))
            
            i = 0
            
            #logging.info("length of ships to move is " + str(len(ships_to_move)))
            for ship in ships_to_move:
                if out_of_time():
                    break
                if move_towards(ship, target_enemy_ships[i]):
                    i += 1
                    if i == (len(target_enemy_ships)):
                        i = 0
        else:
            # attack nearest enemy ship
            for ship in ships_to_move:
                if out_of_time():
                    break
                entities_by_distance = game_map.nearby_entities_by_distance(ship)
                entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
                closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id]
                
                move_towards(ship, closest_enemy_ships[0])

    # Send our set of commands to the Halite engine for this turn
    #logging.info(str(command_queue))
    avoid_dock_conflicts()
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
