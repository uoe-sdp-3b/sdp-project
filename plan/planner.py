import math
import logging

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
        if not self.world():
            return

        self.clear_robot_responses()
        while True:
            command = ""

            v1 =  self.world()['ally'][self.us]["center"]      # our robot's coordinates
            v2 =  self.world()["ball_center"] # ball's coordinates
            robot_dir_vector = self.world()['ally'][self.us]["orientation"]
            log.debug(v1)
            log.debug(v2)
            log.debug(robot_dir_vector)

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $"

            distance = self.dist(v1, v2)

            if distance <= 10:
                break
            else:
                command += "forward " + str(int(math.ceil(0.7 * distance)))  # * 0.8
                self.robot.compose(command)

                # !! Can be written differently if can interrupt robot's previous command
                # !! Can check for response == success
                self.wait_for_robot_response()
                self.clear_robot_responses()

                # Alternative: sleep(5)

        command = ""
        command += "open $"
        command += "forward " + str(int(math.ceil(distance))) + " $"
        command += "stop"

        self.robot.compose(command)

        self.wait_for_robot_response()

        # !! Should check if ball was got with IR (or vision)
        # !! Call get_ball() recursively if not

        self.clear_robot_responses()

    def get_to(self, location):
        if not self.world():
            return

        self.clear_robot_responses()
        while True:
            command = ""

            v1 =  self.world()['ally'][self.us]["center"] # our robot's coordinates
            v2 =  location
            robot_dir_vector = self.world()['ally'][self.us]["orientation"]

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $"

            distance = self.dist(v1, v2)

            if distance <= 10:
                break
            else:
                command += "forward " + str(int(math.ceil(0.7 * distance)))  # * 0.8
                self.robot.compose(command)

                # !! Can be written differently if can interrupt robot's previous command
                # !! Can check for response == success
                self.wait_for_robot_response()
                self.clear_robot_responses()

        self.robot.compose(command)

        self.wait_for_robot_response()
        self.clear_robot_responses()

    # PART 1
    def receive_pass(self):

        v1 =  self.world()['ally'][self.us]["center"]      # our robot's coordinates
        v2 =  self.world()["ball_center"] # ball's coordinates
        robot_dir_vector = self.world()['ally'][self.us]["orientation"]

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
        command = self.turn_command(turn)

        self.robot.compose(command)

        # !! maybe can wait a bit here
        self.get_ball()


    # PART 2
    def receive_turn_pass(self):

        v1 =  self.world()['ally'][self.us]["center"]
        v2 =  self.world()["ball_center"]
        robot_dir_vector = self.world()['ally'][self.us]["orientation"]

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        self.robot.compose(self.turn_command(turn))

        # !! maybe can wait a bit here
        self.get_ball()

        v1 =  self.world()['ally'][self.us]["center"]
        v2 =  self.world()['ally'][self.ally]["center"]
        robot_dir_vector = self.world()['ally'][self.us]["orientation"]

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        # !! can use one command instead

        command = ""
        command += self.turn_command(turn) + " $ "
        command += self.turn_command("stop") + " $ "
        command += "kick 100"

        self.robot.compose(command)


    # PART 3
    def intercept(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        robot_coordinates =  self.world()['ally'][self.us]["center"]
        green_opp = self.world()['enemy']["green"]["center"]
        pink_opp = self.world()['enemy']["pink"]["center"]

        ball_coordinates =  self.world()["ball_center"]

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

        (enemy_bot, robot_coordinates) = ( (320*0.46,0), (-40,100), (40,-100), (1,0) )

        robot_coordinates =  self.world()['ally'][self.us]["center"]
        green_opp = self.world()['enemy']["green"]["center"]
        pink_opp = self.world()['enemy']["pink"]["center"]

        # !! Not sure if this works
        if green_opp is not None:
            enemy_bot = green_opp
        else:
            enemy_bot = pink_opp

        goal_center = (320*0.46,0)

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
        
    def wait_for_robot_response(self):
        while(True):
            while(self.robot.queue.empty()):
                pass
            response = self.robot.queue.get()
            if response[-1] == '1':
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
