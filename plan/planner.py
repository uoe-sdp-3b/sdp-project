import math
import logging
import time

log = logging.getLogger(__name__)
# STATUS:
# - planner does correct calculations
# - planner does optimal calculations
# - planner has been unit tested
# - at the moment planner just has example vision inputs
# TODO:
# - link planner to comms
# - link planner to vision API
# - make planner iteratively change robot's current action plan based on vision
# - make planner conform with milestone 3 requirements
# - make planner run specifically when we need it (possibly in the backgroud?)

# - Decide how we want to work out where to move to to recieve a pass
# - Decide how we want to work out who defender is. i.e. from being in defense area or via comms with other team
# - Also, I've written some more small todos futher down the program
# - -- Calum


class Planner(object):

    def __init__(self, world_api, our_color, robot, debug=False):
        if debug:
            log.setLevel(logging.DEBUG)

        self.world_api = world_api
        self.robot = robot

        if our_color == 'green':
            self.us = our_color
            self.ally = 'pink'
        else:
            self.us = 'pink'
            self.ally = our_color


    # MILESTONE 1 planning task

    def world(self):
        return self.world_api.world

    def close(self):
        """
        Gracefully close everything that the planner depends on
        """
        self.world_api.close()

    def strategy(self):
        # This should be the overall wrapper / strategy

        state = 0

        while(True):

            if(state == 0):
                # Firstly, we need to find out who has the ball / where it is

                who = who_has_ball()

                if(ball_caught()):
                    # If we have the ball
                    state = 1
                elif who == "ally":
                    # If our teammate has the ball
                    state = 2
                elif (who == "pink_opponent" or who == "green_opponent"):
                    # If an enemy has the ball
                    state = 3
                else:
                    # If the ball is free on the pitch
                    state = 4

            elif(state == 1):
                # This is the state we are in when we have the ball in our grabber
                # If we are close enough to the enemy goal, we should attempt to shoot
                # Otherwise, we should attempt a pass
                if(close_enough_to_shoot()):
                    score()
                else:
                    pass_to_teammate()
                state = 0

            elif(state == 2):
                # This is the state we are in when our teammate has the ball
                # If the teammate is close enough to score, we should try and move back and defende
                # Otherwise, we should try and move forward enough to be in a position to receive a pass

                if(teammate_close_enough_to_shoot):
                    defend()
                else :
                    move_to_recieve()
                    receive_pass()
                state = 0

            elif(state == 3):
                # This is the state we are in if an enemy robot has the ball
                # If we are designated as the defender somehow, we should stay in the defense box
                # Otherwise, we should move and try to intercept the ball from opponents' kicks

                if(is_defender):
                    defend()
                else:
                    intercept()
                state = 0

            elif(state == 4):
                # This is the state we are in if no-one has the ball
                # If we are the closest robot to the ball, then we should try and grab the ball quick;y
                # Otherwise, we should go and try and defend the goal

                if(closest_to_ball):
                    get_ball()
                else:
                    defend()
                state = 0


    # x - forward distance
    # y - right distance
    # z angle to the right of x
    # Note: this function is perfect for validating if communications work
    #       without flaws
    def xyzmove(self, x, y, z):
        x = int(x)
        y = int(y)
        z = int(z)

        command = ""

        if x > 0:
            command += "forward " + str(abs(x)) + " $ stop $ "
        elif x < 0:
            command += "backward " + str(abs(x)) + " $ stop $ "

        total_turn = 0
        turn = 90

        if y > 0:
            total_turn += turn
            command += "right " + str(turn) + " $ "
            command += "forward " + str(abs(y)) + " $ stop $ "
        elif y < 0:
            total_turn -= turn
            command += "left " + str(turn) + " $ "
            command += "forward " + str(abs(y)) + " $ stop $ "
        angle_remaining = (z - total_turn) % 360

        # Mod 360 to avoid treachery
        if angle_remaining <= 180:
            command += "right " + str(angle_remaining)
        else:
            command += "left " + str(360 - angle_remaining)

        # self.compose(command)

    # MILESTONE 3 planning tasks

    # CORE functions

    def get_ball(self):
        world = self.world()
        if not world:
            return

        self.clear_robot_responses()
        while True:
            world = self.world()
            
            command = ""

            log.debug(">>>")
            log.debug(world)


            v1 =  world['ally'][self.us]["center"]      # our robot's coordinates
            v2 =  world["ball_center"] # ball's coordinates
            robot_dir_vector = world['ally'][self.us]["orientation"]

            if v1 is None or v2 is None or robot_dir_vector is None:
                continue
            
            print "v1 ", v1
            print "v2 ", v2
            print "dirv ", robot_dir_vector
            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $ stop $ "

            distance = self.dist(v1, v2)
            print(distance)

            if distance <= 80:
                if distance < 30:
#                    self.clear_robot_responses()
                    self.robot.compose("backward 10")
#                    self.wait_for_robot_response()
                    time.sleep(3)
#                    self.clear_robot_responses()
                break
            else:
                command += " forward " + str(int(0.25 * distance))  # * 0.8
#                self.clear_robot_responses()
                self.robot.compose(command)

                # !! Can be written differently if can interrupt robot's previous command
                # !! Can check for response == success
                # self.wait_for_robot_response()
#                self.wait_for_robot_response()
                time.sleep(5)
#                self.clear_robot_responses()

                # Alternative: sleep(5)

        command = ""
        command += self.turn_command(turn) + " $ stop $"
        command += "open_grabber $"
        command += "forward " + str(int(0.58 * math.ceil(distance))) + " $"
        command += "close_grabber"
#        self.clear_robot_responses()
#        self.robot.compose(command)
#        self.wait_for_robot_response()
#        self.clear_robot_responses()
        time.sleep(2)
        
        self.robot.compose("read_infrared")

        if not self.ball_caught():
            print "Trying again"
#            self.clear_robot_responses()
            self.robot.compose("open_grabber")
            self.robot.compose("backward 20")
            self.robot.compose("stop")
#            self.wait_for_robot_response()
            time.sleep(2)
#            self.clear_robot_responses()
            self.get_ball()



    def get_to(self, location):
        world = self.world()
        if not world:
            return

        self.clear_robot_responses()
        while True:
            world = self.world()
            command = ""

            v1 =  world['ally'][self.us]["center"] # our robot's coordinates
            v2 =  location
            robot_dir_vector = world['ally'][self.us]["orientation"]

            if v1 is None or v2 is None or robot_dir_vector is None:
                continue

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $ stop $"

            distance = self.dist(v1, v2)

            if distance <= 40:
                break
            else:
                command += "forward " + str(int(0.30 * distance))  # * 0.8
                self.robot.compose(command)

                # !! Can be written differently if can interrupt robot's previous command
                # !! Can check for response == success
                # self.wait_for_robot_response()
                time.sleep(4)
                self.clear_robot_responses()

        self.robot.compose(command)

        self.wait_for_robot_response()
        self.clear_robot_responses()

    # PART 1
    def receive_pass(self):

        try:
            v1 =  self.world()['ally'][self.us]["center"]      # our robot's coordinates
            v2 =  self.world()["ball_center"] # ball's coordinates
            robot_dir_vector = self.world()['ally'][self.us]["orientation"]


            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command = self.turn_command(turn)

            self.robot.compose(command)
        except:
            print("exception in receive pass")

        # !! maybe can wait a bit here
        self.get_ball()


    def test(self):
        self.get_ball()

        def turn_to_teammate():
            world = self.world()
            v1 =  world['ally'][self.us]["center"]
            v2 =  world['ally'][self.ally]["center"]
            robot_dir_vector = world['ally'][self.us]["orientation"]


            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

            # !! can use one command instead

            command = ""
            command += self.turn_command(turn) + " $ "
            command += self.turn_command("stop")
            self.robot.compose(command)

        turn_to_teammate()
        turn_to_teammate()

        self.robot.compose("kick 100")
    # PART 2
    def receive_turn_pass(self):

        # world = self.world()
        # v1 =  world['ally'][self.us]["center"]
        # v2 =  world["ball_center"]
        # robot_dir_vector = world['ally'][self.us]["orientation"]


        # turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        # self.robot.compose(self.turn_command(turn))

        # time.sleep(2)

        # !! maybe can wait a bit here
        self.get_ball()

        def turn_to_teammate():
            while True:
                world = self.world()
                v1 =  world['ally'][self.us]["center"]
                v2 =  world['ally'][self.ally]["center"]
                robot_dir_vector = world['ally'][self.us]["orientation"]

                if v1 is not None and v2 is not None and robot_dir_vector is not None:
                    break

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

            # !! can use one command instead

            command = ""
            command += self.turn_command(turn) + " $ stop $"
            self.robot.compose(command)

        turn_to_teammate()

        self.robot.compose("kick 100")


    # PART 3
    def intercept(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        while True:
            world = self.world()
            robot_coordinates =  world['ally'][self.us]["center"]
            green_opp = world['enemy']["green"]["center"]
            pink_opp = world['enemy']["pink"]["center"]

            ball_coordinates =  self.world()["ball_center"]

            if robot_coordinates is not None and green_opp is not None and pink_opp is not None and ball_coordinates is not None:
                break


        # Choose the opponent which is not near the ball
        if self.dist(ball_coordinates, green_opp) > self.dist(ball_coordinates, pink_opp):
            other_bot = green_opp
        else:
            other_bot = pink_opp

        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (ball_coordinates[1] - other_bot[1]) / (ball_coordinates[0] - other_bot[0])

        # m = y - kx
        m = other_bot[1] - k * other_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x,y)

        self.get_to(i_location)


    def defend(self):
        # !! this is simplest possible strategy
        # !! can change to robot seeking ball within confined defence area
        while True:
            world = self.world()
            robot_coordinates =  world['ally'][self.us]["center"]
            green_opp = world['enemy']["green"]["center"]
            pink_opp = world['enemy']["pink"]["center"]

            if robot_coordinates is not None and (green_opp is not None or pink_opp is not None):
                break

        # !! Not sure if this works
        if green_opp is not None:
            enemy_bot = green_opp
        else:
            enemy_bot = pink_opp

        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (goal_center[1] - enemy_bot[1]) / (goal_center[0] - enemy_bot[0])

        # m = y - kx
        m = enemy_bot[1] - k * enemy_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x,y)

        self.get_to(i_location)


    def score(self):
        # Should attempt to kick ball directly at the enemy goal
        # This assumes the robot is already in a suitable position to score a goal
        # Also assumes the robot currently has the ball in the kicker

        # Need to get robot's current position and heading
        # Also need goal location

        while True:
            world = self.world()
            robot_coordinates =  world['ally'][self.us]["center"]
            robot_dir_vector = world['ally'][self.us]["orientation"]
            goal_location  = goal_centre[0]
            #TODO make sure this is the right goal
            if robot_coordinates is not None and (robot_dir_vector is not None) and (goal_location is not None):
                break

        # Firstly, turn to face goal

        turn_angle = angle_a_to_b(robot_coordinates, goal_location,robot_dir_vector)
        command = ""
        command += self.turn_command(turn_angle) + "$ stop $"

        # next, kick at goal
        command += "kick 100 $"

        self.robot.compose(command)
        self.wait_for_robot_response()
        self.clear_robot_responses()


    def pass_to_teammate(self):

        while True:
            world = self.world()
            v1 =  world['ally'][self.us]["center"]
            v2 =  world['ally'][self.ally]["center"]
            robot_dir_vector = world['ally'][self.us]["orientation"]
            if v1 is not None and v2 is not None and robot_dir_vector is not None:
                break

        turn_angle = angle_a_to_b(v1,v2, robot_dir_vector)
        command = ""
        command += self.turn_command(turn_angle) + "$ stop $"

        command += "kick 100 $"

        self.robot.compose(command)
        self.wait_for_robot_response()
        self.clear_robot_responses()


    # AUXILIARY functions
    def angle_between(self, p1, p2):
        ang1 = math.atan2(*p1[::-1])
        ang2 = math.atan2(*p2[::-1])
        return math.degrees((ang1 - ang2))

    def angle_a_to_b(self, r, b, dirv):
        if type(dirv[1]) == list:
            dv = dirv[1]
        else:
            dv = dirv

        d = (b[0] - r[0], b[1] - r[1])
        return self.angle_between(d, dv)

    def dist(self, v1, v2):
        return math.hypot(v1[0] - v2[0], v1[1] - v2[1])

    def ball_caught(self):
        start_time_1 = time.time()
        while True:
            while(self.robot.queue.empty()):
                pass
            response = self.robot.queue.get()
            if response == 'y':
                print "BALL CAUGHT"
            
            if response in ['y','n']:
                return response == 'y'
            x = self.millis(start_time_1)
            if(x > 800):
                return False

    def millis(self, start_time):
        st = int(round(start_time * 1000))
        ms = int(round(time.time() * 1000))
        return ms-st

    def wait_for_robot_response(self):
        start_time_1 = time.time()
        while(True):
            while(self.robot.queue.empty()):
                pass
            response = self.robot.queue.get()
            if response[2] == '1':
                break
            x = self.millis(start_time_1)
            if(x > 800):
                break


    def clear_robot_responses(self):
        # Empty response queue
        while(not self.robot.queue.empty()):
            self.robot.queue.get()

    # Returns string "[left/right]  [turn degrees (<=180)]"
    def turn_command(self, turn):
        if turn < 0:
            turn = abs(turn)
            if turn <= 180:
                command = "right " + str(abs(int(turn)))
            else:
                command = "left " + str(360 - abs(int(turn)))
        else:
            if turn <= 180:
                command = "left " + str(abs(int(turn)))
            else:
                command = "right " + str(360 - abs(int(turn)))

        return command

    #TODO - implement these functions


    def is_defender(self):
        # TODO - function should check to see if we are the defender on our team, e.g. by seeing if we are in the defense box
        pass

    def close_enough_to_shoot(self):
        # function should determine if the robot is close enough to the enemy goal to shoot, or if it should attempt a pass
        # maybe also need a similar one for the teammate

        while True:
            world = self.world()
            v1 =  world['ally'][self.us]["center"]
            goal_location  = goal_centre[0]
            #TODO make sure this is the right goal
            if v1 is not None and goal_location is not None:
                break

        xdiff = goal_location[0] - v1[0]
        ydiff = goal_location[1] - v1[1]

        diff = sqrt(xdiff **2 + ydiff ** 2)

        if (diff < 80):
            return True
        else:
            return False
        #TODO Fix threshold value

    def teammate_close_enough_to_shoot(self):
        # see above

        while True:
            world = self.world()
            v1 =  world['ally'][self.ally]["center"]
            goal_location  = goal_centre[0]
            #TODO make sure this is the right goal
            robot_dir_vector = world['ally'][self.us]["orientation"]
            if v1 is not None and goal_location is not None:
                break

        xdiff = goal_location[0] - v1[0]
        ydiff = goal_location[1] - v1[1]

        diff = sqrt(xdiff **2 + ydiff ** 2)

        if (diff < 80):
            return True
        else:
            return False
        #TODO Fix threshold value

    def closest_to_ball(self):
        # function should tell us which robot is the closest to the ball on the pitch

        while True:
            world = self.world()
            v1 =  world['ally'][self.us]["center"]
            v2 =  world['ally'][self.ally]["center"]
            green_opp = world['enemy']["green"]["center"]
            pink_opp = world['enemy']["pink"]["center"]
            ball_coordinates =  self.world()["ball_center"]

            if v1 is not None and v2 is not None and green_opp is not None and pink_opp is not None:
                break

        v1b = dist(v1, ball_coordinates)
        v2b = dist(v2, ball_coordinates)
        gb = dist(green_opp, ball_coordinates)
        pb = dist(pink_opp, ball_coordinates)

        dists = [v1b, v2b, gb, pb]
        robots = ["us", "ally", "green_opponent", "pink_opponent"]

        ind = dists.index(min(dists))
        robot = robots[ind]
        dist = dists[ind]

        return[robot, dist]

    def move_to_recieve(self):
        # TODO - Function should allow us to move to a better position to receive a pass
        pass

    def who_has_ball(self):
        # TODO - Should return who has the ball currently.
        # Should work by calling closest_to_ball, and then if the difference between that robot and the ball is small enough,
        # then it is determined to 'have' the ball

        [robot, dist] = closest_to_ball()

        if dist < 15:
            #TODO check threshold value
            return robot
        else:
            return "no-one"
