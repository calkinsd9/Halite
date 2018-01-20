"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
import math
import time

def dock_ship_to_planet(ship, planet):
    if planet not in planets_being_docked:
        command_queue.append(ship.dock(planet))
        planets_being_docked.append(planet)
    else:
        return False
    
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
    # else, skip turn

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("TheGeneral")
# Then we print our start message to the logs
logging.info("Starting my TheGeneral bot!")

harasser_list = []

while True:
    # TURN START
    
    # if ships are low (3), max_corrections=90, angular_step=1
    # as ships reach 80, max_corrections=18, angular_step=5
        
    t0 = time.time()
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    
    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    
    all_my_ships_list = game_map.get_me().all_ships()
    all_my_ships_ids_list = [ship.id for ship in all_my_ships_list]
    number_of_total_ships = len(all_my_ships_list)
    
    MAX_CORRECTIONS_SLIDER = 90 - (number_of_total_ships - 3)
    ANGULAR_STEP_SLIDER = 5-(int((number_of_total_ships-3)/20))

        
    undocked_ship_list = [ship for ship in game_map.get_me().all_ships() if ship.docking_status == ship.DockingStatus.UNDOCKED]
    
    # clear the list of planets being docked
    planets_being_docked = []
    
    # early game
    if number_of_total_ships < 20:
        harasser_fleet_size = number_of_total_ships // 3
        logging.info("harasser fleet size is " + str(harasser_fleet_size))
        
        harasser_list = []
        
        # get all non-harasser ships
        non_harasser_list = [ship for ship in all_my_ships_list if ship not in harasser_list]
        
        logging.info("non-harasser list: " + str(non_harasser_list))
        
        # assign new harassers
        logging.info("assigning new harassers")
        
        non_harasser_nearest_enemy_dict = {}
        
        # get all non-docked ships that aren't harassers
        non_harasser_not_docked_list = [ship for ship in all_my_ships_list if ship.docking_status == ship.DockingStatus.UNDOCKED]
        
        # pair each not-docked non-harasser ship with its distance to its nearest enemy
        for ship in non_harasser_not_docked_list:
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
        
            closest_enemy_ship = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id][0]
            
            # pair each non harasser ship with the distance to nearest enemy 
            non_harasser_nearest_enemy_dict[ship] = ship.calculate_distance_between(closest_enemy_ship)
            
        # assign new harassers accordingly
        for i in range(harasser_fleet_size):
            if len(non_harasser_nearest_enemy_dict.keys()) == 0:
                break
            
            # get the ship with the shortest distance to its enemy
            new_harasser = min(non_harasser_nearest_enemy_dict, key=non_harasser_nearest_enemy_dict.get)
        
            # add it to the harasser list
            harasser_list.append(new_harasser)
            logging.info("new harasser from undocked is ship " + str(new_harasser.id))
            
            # remove it from the dictionary
            non_harasser_nearest_enemy_dict.pop(new_harasser)

            harasser_fleet_size -= 1
            


        # if we ran out of undocked ships to make into harassers, pull from the docked ships
        if harasser_fleet_size > 0:
            # pull from the docked ships now
            for ship in [ship for ship in all_my_ships_list if ship.docking_status != ship.DockingStatus.UNDOCKED]:
                entities_by_distance = game_map.nearby_entities_by_distance(ship)
            
                closest_enemy_ship = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id][0]
                
                # pair each non harasser ship with the distance to nearest enemy 
                non_harasser_nearest_enemy_dict[ship] = ship.calculate_distance_between(closest_enemy_ship)
              
            # assign new harassers accordingly
            for i in range(harasser_fleet_size):
                # get the ship with the shortest distance to its enemy
                new_harasser = min(non_harasser_nearest_enemy_dict, key=non_harasser_nearest_enemy_dict.get)
                
                # add it to the harasser list
                harasser_list.append(new_harasser)
                logging.info("new harasser from docked is ship " + str(new_harasser.id))


                # remove it from the dictionary
                non_harasser_nearest_enemy_dict.pop(new_harasser)

                if len(non_harasser_nearest_enemy_dict.keys()) == 0:
                    break
                
        # assign commands
        # harasser logic
        for ship in harasser_list:
            # navigate toward nearest docked enemy ship
            entities_by_distance = game_map.nearby_entities_by_distance(ship)

            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id and entities_by_distance[distance][0].docking_status != entities_by_distance[distance][0].DockingStatus.UNDOCKED]

            if not closest_enemy_ships:
                closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id]
            
            logging.info("ship " + str(ship.id) + "is moving toward ship " + str(closest_enemy_ships[0].id))
            move_towards(ship, closest_enemy_ships[0])
        
        # non-harasser logic
        # Get a list of all ships that aren't docked 
        ships_to_move = [ship for ship in game_map.get_me().all_ships() if ship.docking_status == ship.DockingStatus.UNDOCKED]
        ships_to_move = [ship for ship in ships_to_move if ship not in harasser_list]
        ships_moved = []
        
        # get list of all the planets that are not owned or are owned by me, but not full
        unowned_planets_or_dockable_I_own = [planet for planet in game_map.all_planets() if planet.is_owned() == False or (planet.owner.id == game_map.get_me().id and len(planet.all_docked_ships()) != planet.num_docking_spots)]
        
        # dictionary of planets matched to max ships targeting
        planet_targets_dict = {planet:(planet.num_docking_spots - len(planet.all_docked_ships())) for planet in unowned_planets_or_dockable_I_own}
            
        # I want each ship to fly toward the nearest planet (to them) in the target list
        # once the max # of ships are headed there, it's no longer a viable destination
        for ship in ships_to_move:
            # if there are no more planet destinations, break
            if len(planet_targets_dict.keys()) == 0:
                break
            
            # get list of nearest planets to this ship
            nearest_planets = sorted(list(planet_targets_dict.keys()), key=ship.calculate_distance_between)
            
            nearest_planet = nearest_planets[0]
            
            # If the ship can dock, dock do it
            if ship.can_dock(nearest_planet):
                dock_ship_to_planet(ship, nearest_planet)
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
            
        # take moved ships out of "to move" list
        for ship in ships_moved:
            ships_to_move.remove(ship)

        if ships_to_move:
            # if still ships to move, attack nearest enemy
            for ship in ships_to_move:
                entities_by_distance = game_map.nearby_entities_by_distance(ship)
                
                closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id]
                
                move_towards(ship, closest_enemy_ships[0])

    # mid-late-game
    else:            
        number_colonizers = int(len(all_my_ships_list) * .1)
        
        planet_targets = [planet for planet in game_map.all_planets() if planet.is_owned() == False or planet.owner.id != game_map.get_me().id]
        
        planets_distance_to_me_dict = {}
        
        for planet in planet_targets:
            entities_by_distance = game_map.nearby_entities_by_distance(planet)
            
            my_nearest_ship = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id == game_map.get_me().id][0]
            
            planets_distance_to_me_dict[planet] = my_nearest_ship.calculate_distance_between(planet)
            
        planets_ranked = sorted(planets_distance_to_me_dict.keys(), key=planets_distance_to_me_dict.get)

        i = 0
        
        for planet in planets_ranked:
            if i > number_colonizers:
                break

            entities_by_distance = game_map.nearby_entities_by_distance(planet)
            
            closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id and entities_by_distance[distance][0].docking_status == entities_by_distance[distance][0].DockingStatus.UNDOCKED]
            
            if not closest_enemy_ships:
                break
                
            closest_enemy_ship = closest_enemy_ships[0]
            
            if closest_enemy_ship.calculate_distance_between(planet) < 30:
                continue
                            
            closest_friendy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id == game_map.get_me().id and entities_by_distance[distance][0].docking_status == entities_by_distance[distance][0].DockingStatus.UNDOCKED]
            
            if not closest_friendy_ships:
                break
                
            closest_friendy_ship = closest_friendy_ships[0]
            
            if closest_friendy_ship.can_dock(planet):
                dock_ship_to_planet(closest_friendy_ship, planet)
                undocked_ship_list.remove(closest_friendy_ship)
            else:
                if planet.is_owned():
                    move_towards(closest_friendy_ship, closest_enemy_ship)
                    undocked_ship_list.remove(closest_friendy_ship)
                else:
                    move_towards(closest_friendy_ship, planet)
                    undocked_ship_list.remove(closest_friendy_ship)
                    
            i += 1
        
        for ship in undocked_ship_list:
            t1 = time.time()
            
            if t1-t0 > (.9 * 2):
                break
            # move toward nearest enemy
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            
            closest_enemy_ship = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id][0]
            
            move_towards(ship, closest_enemy_ship)
            
    
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
