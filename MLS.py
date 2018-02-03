import hlt
import logging
import math
import time
from collections import OrderedDict
            
def out_of_time():
    t1 = time.time()
    if (t1-t0) > (.90 * 2):
        return True
    return False
    
def move_towards(ship, entity):
    navigate_command = ship.navigate(
                ship.closest_point_to(entity),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                avoid_obstacles=True,
                max_corrections=90,
                angular_step=1,
                ignore_ships=False)
    if navigate_command:
        command_queue.append(navigate_command)
        return True
    else:
        return False
    # else, skip turn
    
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1]) #Typo was here

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       # raise Exception('lines do not intersect')
       return True

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    # return x, y
    return False
    
def avoid_friendly_collisions():
    for i in range(len(command_queue)):
        command = command_queue[i].split()
        # get location of ship
        logging.info(command)
        logging.info(str(int(command[1])))
        logging.info(all_my_ships_list)
        ship1 = [s for s in all_my_ships_list if s.id == int(command[1])]
        ship1 = ship1[0]
        current_position1 = [ship1.x, 0-ship1.y]
        thrust = command[2]
        angle = math.radians(float(command[3]))
        x_movement = hlt.constants.MAX_SPEED * math.sin(angle)
        y_movement = 0.0 - hlt.constants.MAX_SPEED*math.cos(angle)
        new_position1 = [current_position1[0] + x_movement, current_position1[1] + y_movement]
        
        for j in range(i+1, len(command_queue)):
            command = command_queue[j].split()
            # get location of ship
            ship2 = [s for s in all_my_ships_list if s.id == int(command[1])]
            ship2 = ship2[0]
            current_position2 = [ship2.x, 0-ship2.y]
            thrust = command[2]
            angle = math.radians(float(command[3]))
            x_movement = hlt.constants.MAX_SPEED * math.sin(angle)
            y_movement = 0.0 - hlt.constants.MAX_SPEED*math.cos(angle)
            new_position2 = [current_position2[0] + x_movement, current_position2[1] + y_movement]
            
            if line_intersection((current_position1, new_position1), (current_position2, new_position2)):
                # if they're on the same line, let them continue if they're far enough away from each other
                if ship1.calculate_distance_between(ship2) > 7:
                    continue
                logging.info("INTERSECTION")
                return j
                
    return None
            

# GAME START
game = hlt.Game("MLS")
logging.info("Starting my MLS bot!")

turn = 0

ships_to_targets = {}

while True:
    t0 = time.time()

    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    
    turn += 1
    
    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    
    all_my_ships_list = game_map.get_me().all_ships()
    
    enemy_ships = [ship for ship in game_map._all_ships() if ship.owner.id != game_map.get_me().id]
    
    enemy_ship_ids = [enemy.id for enemy in enemy_ships]
    
        
    if turn == 1:
        # assign ships to enemy, 1 to 1
        for i in range(len(all_my_ships_list)):
            ships_to_targets[all_my_ships_list[i].id] = enemy_ships[i].id

    # move toward your assigned enemy
    for ship in all_my_ships_list:
        if out_of_time():
            break
        # if enemy is still alive, pursue
        if ships_to_targets[ship.id] in enemy_ship_ids:
            target = [enemy for enemy in enemy_ships if enemy.id ==ships_to_targets[ship.id]][0]

            move_towards(ship, target)
        else:
            # pursue nearest enemy
            entities_by_distance = game_map.nearby_entities_by_distance(ship)
            entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
        
            closest_enemy_ship = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].owner.id != game_map.get_me().id][0]
            
            move_towards(ship, closest_enemy_ship)
            
    bad_move = avoid_friendly_collisions()
    
    if bad_move:
        command_queue.pop(bad_move)
    
    game.send_command_queue(command_queue)
    logging.info(command_queue)
    # TURN END
# GAME END
