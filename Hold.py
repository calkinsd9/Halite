#!/usr/bin/env python3
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
from collections import OrderedDict
from enum import Enum
import time

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

def out_of_time():
    t1 = time.time()
    if (t1-t0) > (.95 * 2):
        return True
    return False


# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Latest-v5")
# Then we print our start message to the logs
logging.info("Starting my Bot!")

turn = 0
protector_list = []

Direction = Enum('Direction', 'N E S W')

team_ships_id_list = []

while True:
    t0 = time.time()
    game_map = game.update_map()
    command_queue = []
    player_id = game_map.get_me().id
    team_ships = game_map.get_me().all_ships()
    
    MAX_CORRECTIONS_SLIDER = 90 - (len(team_ships) - 3)
    if MAX_CORRECTIONS_SLIDER < 18:
        MAX_CORRECTIONS_SLIDER = 18
    ANGULAR_STEP_SLIDER = int((4/77 * len(team_ships) + 1))
    if ANGULAR_STEP_SLIDER > 5:
        ANGULAR_STEP_SLIDER = 5
    
    all_planets = game_map.all_planets()
    my_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id == player_id]
    enemy_planets = [planet for planet in game_map.all_planets() if planet.is_owned() and planet.owner.id != player_id]
    enemy_planets_by_radius = list(sorted(enemy_planets, key = lambda t: t.radius))

    ships_to_move = [ship for ship in game_map.get_me().all_ships() if ship.docking_status == ship.DockingStatus.UNDOCKED]
    
    ships_moved = []
    
    all_enemy_ships = []
    for p in game_map.all_players():
        if p.id != player_id and len(p.all_ships()) > 0:
            all_enemy_ships.extend(p.all_ships())
    
    if turn == 0:
        logging.info("ship 0 (x,y): " + str(team_ships[0].x) + "," + str(team_ships[0].y))
        logging.info("ship 1 (x,y): " + str(team_ships[1].x) + "," + str(team_ships[1].y))
        logging.info("ship 2 (x,y): " + str(team_ships[2].x) + "," + str(team_ships[2].y))
        team_ships_id_list = [ship.id for ship in team_ships]
        unit_number = len(team_ships_id_list)
        meridian = game_map.width/2
        equator = game_map.height/2
        if team_ships[0].x < meridian and team_ships[1].x < meridian and team_ships[2].x < meridian:
            direction = Direction.W
        elif team_ships[0].x > meridian and team_ships[1].x > meridian and team_ships[2].x > meridian:
            direction = Direction.E
        elif team_ships[0].y < equator and team_ships[1].y < equator and team_ships[2].y < equator:
            direction = Direction.N
        else:
            direction = Direction.S
    else:
        new_ship_ids = [ship.id for ship in team_ships if ship.id not in team_ships_id_list]
        logging.info("new ships list len: " + str(len(new_ship_ids)))
        for id in new_ship_ids:
            unit_number += 1
            if unit_number % 3 == 0:
                protector_list.append(id)
        team_ships_id_list = [ship.id for ship in team_ships]
    
#        if turn % 10 == 0:
        x_inc = (game_map.width-meridian)*1.0/(300-turn)
        y_inc = (game_map.height-equator)*1.0/(300-turn)
        
        logging.info("protector list len: " + str(len(protector_list)))
        logging.info("x_inc: " + str(x_inc))
        logging.info("y_inc" + str(y_inc))
        
        if direction == Direction.W:
            meridian += x_inc
        elif direction == Direction.E:
            meridian -= x_inc
        elif direction == Direction.N:
            equator += y_inc
        else:
            equator -= y_inc
        
    turn += 1

    logging.info("meridian: " + str(meridian))
    logging.info("direction: " + str(direction))
    logging.info("equator: " + str(equator))
    
    for ship in ships_to_move:
        if out_of_time():
            break
        
        can_move = False
        if(direction == Direction.N) and ship.y <= equator:
            can_move = True
        elif(direction == Direction.E) and ship.x >= meridian:
            can_move = True
        elif(direction == Direction.S) and ship.y >= equator:
            can_move = True
        elif(direction == Direction.W) and ship.x <= meridian:
            can_move = True
            
        if not can_move:
            continue
        
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key = lambda t: t[0]))
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and (not entities_by_distance[distance][0].is_owned() or (entities_by_distance[distance][0].is_owned and entities_by_distance[distance][0].owner.id == player_id and not entities_by_distance[distance][0].is_full()))]
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0] not in team_ships]
#        closest_docked_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].DockingStatus.DOCKED and entities_by_distance[distance][0] not in team_ships]
#        closest_undocked_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and entities_by_distance[distance][0].DockingStatus.UNDOCKED and entities_by_distance[distance][0] not in team_ships]
        
#        if(direction == Direction.N):
#            enemy_ships_across_line = [s for s in closest_enemy_ships if s.y >= equator]
#        elif(direction == Direction.E):
#            enemy_ships_across_line = [s for s in closest_enemy_ships if s.x >= meridian]
#        elif(direction == Direction.S):
#            enemy_ships_across_line = [s for s in closest_enemy_ships if s.y <= equator]
#        elif(direction == Direction.W):
#            enemy_ships_across_line = [s for s in closest_enemy_ships if s.x <= meridian]
        
        if(direction == Direction.N):
            planets_in_hemi = [p for p in closest_empty_planets if p.y >= equator]
        elif(direction == Direction.E):
            planets_in_hemi = [p for p in closest_empty_planets if p.x >= meridian]
        elif(direction == Direction.S):
            planets_in_hemi = [p for p in closest_empty_planets if p.y <= equator]
        elif(direction == Direction.W):
            planets_in_hemi  = [p for p in closest_empty_planets if p.x <= meridian]

#        logging.info("num across " + str(len(enemy_ships_across_line)))
        
        if ship in protector_list:
            if move_towards(ship, closest_enemy_ships[0]):
                continue
            else:
                continue
        elif planets_in_hemi:
            planets_in_hemi = list(sorted(planets_in_hemi, key = lambda t: t.radius, reverse=True))
            if ship.can_dock(planets_in_hemi[0]):
                command_queue.append(ship.dock(planets_in_hemi[0]))
                continue
            if move_towards(ship, planets_in_hemi[0]):
                continue
            else:
                continue
        else:
            if move_towards(ship, closest_enemy_ships[0]):
                continue
            else:
                continue
                    
    game.send_command_queue(command_queue)
                
                
                
                
                
                