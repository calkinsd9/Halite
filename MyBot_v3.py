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

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Hornet")
# Then we print our start message to the logs
logging.info("Starting my Hornet bot!")

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    
    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    
    # Get a list of all ships that aren't docked 
    ships_to_move = [ship for ship in game_map.get_me().all_ships() if ship.docking_status == ship.DockingStatus.UNDOCKED]
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
            # We add the command by appending it to the command_queue
            command_queue.append(ship.dock(nearest_planet))
        else:
            # move toward nearest planet
            navigate_command = ship.navigate(
                ship.closest_point_to(nearest_planet),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False)
            if navigate_command:
                command_queue.append(navigate_command)
            else:
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
        #logging.info("ships left to move")
        
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
                navigate_command = ship.navigate(
                    ship.closest_point_to(target_enemy_ships[i]),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    avoid_obstacles=True,
                    max_corrections=20,
                    angular_step=5,
                    ignore_ships=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                    i += 1
                    if i == (len(target_enemy_ships)):
                        i = 0
        else:
            # attack nearest enemy ship
            for ship in ships_to_move:
                entities_by_distance = game_map.nearby_entities_by_distance(ship)
                closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id]
                navigate_command = ship.navigate(
                    ship.closest_point_to(closest_enemy_ships[0]),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    avoid_obstacles=True,
                    max_corrections=20,
                    angular_step=5,
                    ignore_ships=False)
                if navigate_command:
                    command_queue.append(navigate_command)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
