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

    def __init__(self, world_api, our_color, our_goal, robot, debug=False):
        if debug:
            log.setLevel(logging.DEBUG)

        self.world_api = world_api
        self.robot = robot

        # which side we are playing from
        self.our_goal = our_goal

        if our_goal == "left":
            self.enemy_goal = "right"
        else:
            self.enemy_goal = "left"

        if our_color == 'green':
            self.us = our_color
            self.ally = 'pink'
        else:
            self.us = 'pink'
            self.ally = our_color

        self.goal_center = {
            "left": [-320, 0],
            "right": [320, 0]
        }

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
        INITIAL_STATE = 0
        OUR_POSSESSION = 1
        ALLY_POSSESSION = 2
        ENEMY_POSSESSION = 3
        BALL_FREE = 4

        state = 0

        while(True):
            print "STATE: ", state
            if(state == INITIAL_STATE):
                # Firstly, we need to find out who has the ball / where it is

                who = self.who_has_ball()

                if(self.ball_caught()):
                    # If we have the ball
                    state = OUR_POSSESSION
                elif who == "ally":
                    # If our teammate has the ball
                    state = ALLY_POSSESSION
                elif (who == "pink_opponent" or who == "green_opponent"):
                    # If an enemy has the ball
                    state = ENEMY_POSSESSION
                else:
                    # If the ball is free on the pitch
                    state = BALL_FREE

            elif(state == OUR_POSSESSION):
                # This is the state when we have the ball in our grabber
                # If we are close enough to the enemy goal, we should attempt to shoot
                # Otherwise, we should attempt a pass
                if(self.close_enough_to_shoot()):
                    self.score()
                else:
                    self.pass_to_teammate()
                state = INITIAL_STATE

            elif(state == ALLY_POSSESSION):
                # This is the state we are in when our teammate has the ball
                # If the teammate is close enough to score, we should try and move back and defende
                # Otherwise, we should try and move forward enough to be in a position to receive a pass

                if(self.teammate_close_enough_to_shoot()):
                    self.defend()
                else:
                    self.move_to_receive()
                    self.receive_pass()
                state = INITIAL_STATE

            elif(state == ENEMY_POSSESSION):
                # This is the state we are in if an enemy robot has the ball
                # If we are designated as the defender somehow, we should stay in the defense box
                # Otherwise, we should move and try to intercept the ball from opponents' kicks

                if(self.is_defender()):
                    self.defend()
                else:
                    # between enemies to stop passing?...
                    self.intercept()
                state = INITIAL_STATE

            elif(state == BALL_FREE):
                # This is the state we are in if no-one has the ball
                # If we are the closest robot to the ball, then we should try and grab the ball quick;y
                # Otherwise, we should go and try and defend the goal

                if(self.closest_to_ball()):
                    self.get_ball()
                else:
                    self.defend()
                state = INITIAL_STATE
            else:
                print "Error State, this state should not be reached..."
                state = INITIAL_STATE

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
        # self.clear_robot_responses()

        while True:
            world = self.get_world_frame(us=True, ball=True)
            print "frame received"
            #print world
            v1 = world['ally'][self.us]["center"]  # our robot's coordinates
            v2 = world["ball_center"]  # ball's coordinates
            robot_dir_vector = world['ally'][self.us]["orientation"]
            command = ""

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $ stop $ "

            distance = self.dist(v1, v2)
            print(distance)

            if distance <= 80:
                break
                # if distance < 30:
                #     self.send_and_ack("backward 10")
            else:
                command += " forward " + str(int(0.25 * distance))  # * 0.8
                #self.robot.compose(command)
                #time.sleep(4)
                self.send_and_ack(command)

        command = ""
        command += self.turn_command(turn) + " $ stop $"
        command += "open_grabber $"
        command += "forward " + str(int(0.58 * math.ceil(distance))) + " $"
        command += "close_grabber"

        #self.robot.compose(command)
        #time.sleep(4)
        self.send_and_ack(command)

        self.robot.compose("read_infrared")

        if not self.ball_caught():
            print "Trying again"
            tmp_command = "open_grabber $ backward 20 $ stop"
            #self.robot.compose(tmp_command)
            #time.sleep(2)
            self.send_and_ack(tmp_command)
            self.get_ball()

    def get_to(self, location):

        while True:
            world = self.get_world_frame(us=True)
            command = ""

            v1 = world['ally'][self.us]["center"]  # our robot's coordinates
            v2 = location
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
                time.sleep(4)
                self.clear_robot_responses()

        self.robot.compose(command)

        self.wait_for_robot_response()
        self.clear_robot_responses()

    # PART 1
    def receive_pass(self):

        world = self.get_world_frame(us=True, ball=True)
        v1 = world['ally'][self.us]["center"]      # our robot's coordinates
        v2 = world["ball_center"]  # ball's coordinates
        robot_dir_vector = world['ally'][self.us]["orientation"]
        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
        command = self.turn_command(turn)
        self.robot.compose(command)
        # HACK: sleep here
        time.sleep(2)
        # !! maybe can wait a bit here
        self.get_ball()

    def test(self):
        self.get_ball()

        def turn_to_teammate():
            world = self.world()
            v1 = world['ally'][self.us]["center"]
            v2 = world['ally'][self.ally]["center"]
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
                v1 = world['ally'][self.us]["center"]
                v2 = world['ally'][self.ally]["center"]
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
        world = self.get_world_frame(us=True, enemy=True, ball=True)
        robot_coordinates = world['ally'][self.us]["center"]
        green_opp = world['enemy']["green"]["center"]
        pink_opp = world['enemy']["pink"]["center"]
        ball_coordinates = world["ball_center"]

        # Choose the opponent which is not near the ball
        if self.dist(ball_coordinates, green_opp) > self.dist(ball_coordinates, pink_opp):
            other_bot = green_opp
        else:
            other_bot = pink_opp

        # move robot to further enemy from ball between both enemy robots.
        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (ball_coordinates[1] - other_bot[1]) / (ball_coordinates[0] - other_bot[0])

        # m = y - kx
        m = other_bot[1] - k * other_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x, y)

        self.get_to(i_location)

    def defend(self):
        # !! this is simplest possible strategy
        # !! can change to robot seeking ball within confined defence area
        world = self.get_world_frame(us=True, enemy=True)
        robot_coordinates = world['ally'][self.us]["center"]
        green_opp = world['enemy']["green"]["center"]
        pink_opp = world['enemy']["pink"]["center"]

        # TODO: if defending breaks, this is probably the issue
        # make it use the same frame for calculation.
        ball_owner = self.who_has_ball()
        # !! Not sure if this works
        if ball_owner == "green_opponent":
            enemy_bot = green_opp
        else:
            enemy_bot = pink_opp
        # NOTE: we are currently not checking if no-one has the ball.
        # if so, we assume it is the pink robot...

        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (self.goal_center[self.our_goal][1] - enemy_bot[1]) / (self.goal_center[self.our_goal][0] - enemy_bot[0])

        # m = y - kx
        m = enemy_bot[1] - k * enemy_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x, y)

        self.get_to(i_location)

    def score(self):
        """ aim towards enemy goal and kick """

        world = self.get_world_frame(us=True, ally=True)
        world = self.world()
        robot_coordinates = world['ally'][self.us]["center"]
        robot_dir_vector = world['ally'][self.us]["orientation"]
        goal_location = self.goal_center[self.enemy_goal]

        # Firstly, turn to face goal

        turn_angle = self.angle_a_to_b(robot_coordinates, goal_location, robot_dir_vector)
        command = ""
        command += self.turn_command(turn_angle) + "$ stop $"

        # next, kick at goal
        command += "kick 100"

        self.robot.compose(command)
        time.sleep(2)
        # self.wait_for_robot_response()
        # self.clear_robot_responses()

    def pass_to_teammate(self):

        world = self.get_world_frame(us=True, ally=True)
        v1 = world['ally'][self.us]["center"]
        v2 = world['ally'][self.ally]["center"]
        robot_dir_vector = world['ally'][self.us]["orientation"]

        turn_angle = self.angle_a_to_b(v1, v2, robot_dir_vector)
        command = ""
        command += self.turn_command(turn_angle) + "$ stop $"

        command += "kick 100"

        self.robot.compose(command)
        # self.wait_for_robot_response()
        # self.clear_robot_responses()
        time.sleep(2)

    # AUXILIARY functions
    def angle_between(self, p1, p2):
        try:
            ang1 = math.atan2(*p1[::-1])
            ang2 = math.atan2(*p2[::-1])
            return math.degrees((ang1 - ang2))
        except:
            log.error('failure with angle_between')
            print p1, p2
            return 0

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
        while True:
            while(self.robot.queue.empty()):
                pass
            response = self.robot.queue.get()
            if response == 'y':
                print "BALL CAUGHT"

            if response in ['y', 'n']:
                return response == 'y'

    def millis(self, start_time):
        st = int(round(start_time * 1000))
        ms = int(round(time.time() * 1000))
        return ms-st

    def send_and_ack(self, cmd):
        """
        Sends command and blocks until ack
        """
        print cmd
        self.clear_robot_responses()
        commands = cmd.strip().split("$")
        if commands[-1].strip() == "":
            commands.pop()

        self.robot.compose(cmd)

        last_ack = -1
        no_acks = 0
        while no_acks < len(commands):
            while(self.robot.queue.empty()):
                print "waiting..."
            response = self.robot.queue.get()
            
            print response
            
            if len(response) == 3 and response[1] in ["0", "1"] and response[2] == "1" and response != last_ack:
                no_acks += 1
                last_ack = response[1]

        self.clear_robot_responses()
        print "ending command"

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

    def is_defender(self):
        # TODO - function should check to see if we are the defender on
        # our team,
        # e.g. by seeing if we are in the defense box
        world = self.get_world_frame(us=True, ally=True)

        us = world["ally"][self.us]["center"]
        ally = world["ally"][self.ally]["center"]
        # TODO: fix this crap
        our_goal = self.goal_center[self.our_goal]

        # get our distance
        our_dist = self.dist(us, our_goal)
        # get ally distance
        ally_dist = self.dist(ally, our_goal)

        return our_dist < ally_dist

    def close_enough_to_shoot(self):
        # function should determine if the robot is
        # close enough to the enemy goal to shoot,
        # or if it should attempt a pass
        # maybe also need a similar one for the teammate

        world = self.get_world_frame(us=True)
        v1 = world["ally"][self.us]["center"]
        # TODO: make sure this is the right goal
        goal_location = self.goal_center[self.enemy_goal]

        dist = self.dist(v1, goal_location)

        # TODO Fix threshold value
        if (dist < 400):
            return True
        else:
            return False

    def teammate_close_enough_to_shoot(self):
        # see above

        world = self.get_world_frame(ally=True)
        v1 = world['ally'][self.ally]["center"]
        # TODO make sure this is the right goal
        goal_location = self.goal_center[self.enemy_goal]

        xdiff = goal_location[0] - v1[0]
        ydiff = goal_location[1] - v1[1]

        diff = math.sqrt(xdiff**2 + ydiff**2)

        # TODO Fix threshold value
        if (diff < 80):
            return True
        else:
            return False

    def get_world_frame(self,
                        ally=False,
                        us=False,
                        enemy_pink=False,
                        enemy_green=False,
                        ball=False,
                        enemy=False):
        while True:
            world = self.world()
            if ally and not world['ally'][self.us]["center"]:
                log.debug("We are not here not found")
                continue
            if us and not world['ally'][self.us]["center"]:
                log.debug("Ally not found")
                continue
            if enemy_pink and not world['enemy']["pink"]["center"]:
                log.debug("Enemy pink not found")
                continue
            if enemy_green and not world['enemy']["green"]["center"]:
                log.debug("Enemy green not found")
                continue
            if ball and not world["ball_center"]:
                log.debug("ball not found")
                continue
            cond = (world['enemy']['green']['center'] or world['enemy']['pink']['center'])
            if enemy and not cond:
                log.debug("enemies not found (both)")
                continue

            return world

    def closest_to_ball(self):
        # function should tell us which robot is
        # the closest to the ball on the pitch

        world = self.get_world_frame(ally=True,
                                     us=True,
                                     enemy_pink=True,
                                     enemy_green=True,
                                     ball=True)
        v1 = world['ally'][self.us]["center"]
        v2 = world['ally'][self.ally]["center"]
        green_opp = world['enemy']["green"]["center"]
        pink_opp = world['enemy']["pink"]["center"]
        ball_coordinates = world["ball_center"]

        v1b = self.dist(v1, ball_coordinates)
        v2b = self.dist(v2, ball_coordinates)
        gb = self.dist(green_opp, ball_coordinates)
        pb = self.dist(pink_opp, ball_coordinates)

        dists = [v1b, v2b, gb, pb]
        robots = ["us", "ally", "green_opponent", "pink_opponent"]

        ind = dists.index(min(dists))
        robot = robots[ind]
        dist = dists[ind]

        return[robot, dist]

    def move_to_receive(self):
        """
        Move to middle of pitch (on x-axis),
        while optimising distance from both opposing robots.
        """
        # TODO - Function should allow us to move to a
        # better position to receive a pass
        world = self.get_world_frame(enemy=True)
        green = world['enemy']['green']['center']
        pink = world['enemy']['pink']['center']
        max_y = max(green[1], pink[1])
        min_y = min(green[1], pink[1])

        offset = 100
        if abs(max_y + offset) < abs(min_y + offset):
            chosen_y = max_y + offset
        else:
            chosen_y = min_y - offset

        if chosen_y > 200 or chosen_y < -200:
            chosen_y = 0

        self.get_to((50, chosen_y))

    def who_has_ball(self):
        # TODO - Should return who has the ball currently.
        # Should work by calling closest_to_ball,
        # and then if the difference between that robot and the
        # ball is small enough,
        # then it is determined to 'have' the ball

        [robot, dist] = self.closest_to_ball()

        # TODO check threshold value
        if dist < 50:
            return robot
        else:
            return "no-one"
