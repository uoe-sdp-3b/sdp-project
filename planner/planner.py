import math


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
    def __init__(self):
        # TODO:
        # Add:
        # Link to comms
        # Link to vision

        print("This has begun")

    # MILESTONE 1 planning task

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

    # MILESTONE 2 planning tasks

    # rotate, move and grab
    def move_and_grab(self):

        # distance = 10
        # while(distance >=10):
        command = ""
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        (ball_coordinates, robot_coordinates, robot_dir_vector) = ((0, 0), (75, 75), (0, -1))
        print("expected turn - %d, expected dist - %d" % (-90, 226))

        v1 = robot_coordinates
        v2 = ball_coordinates

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        distance = self.dist(v1, v2)

        command += self.turn_command(turn) + " $"

        command += "forward " + str(int(math.ceil(0.9 * distance))) + " $"  # * 0.8
        # self.compose(command)

        command += "open $"
        command += "forward " + str(int(math.ceil(0.1 * distance))) + " $"
        command += "stop"
        print(command)
        # self.compose(command)

    def rotate_kick(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        (_, robot_coordinates, robot_dir_vector) = ((160, 160), (0, 320*0.46), (0, 1))
        print("expected turn - %d?" % 45)

        v1 = robot_coordinates

        turn = self.angle_a_to_b(v1, (-320*0.46, 0.0), robot_dir_vector)

        command = ""

        command += self.turn_command(turn) + " $"

        command += "kick 100"
        print(command)
        # self.compose(command)

    # MILESTONE 3 planning tasks

    # CORE functions

    def get_ball(self):
        while True:
            command = ""
            # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

            v1 = robot_coordinates
            v2 = ball_coordinates

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $"

            distance = self.dist(v1, v2)

            if distance <= 10:
                break
            else:
                command += "forward " + str(int(math.ceil(0.7 * distance)))  # * 0.8
                # self.compose(command)

                # !! can I override the last command the bot got or not?
                # If *I can't*
                # then sleep(5)

            command += "open $"
            command += "forward " + str(int(math.ceil(distance))) + " $"
            command += "stop"
            # self.compose(command)

            # check with IR if ball got.
            # IF NOT GOT:
            # get_ball()

    def get_to(self, location):
        while True:
            command = ""
            # (robot_coordinates, robot_dir_vector) = get_info(self.camera)

            v1 = robot_coordinates
            v2 = location

            turn = self.angle_a_to_b(v1, v2, robot_dir_vector)
            command += self.turn_command(turn) + " $"

            distance = self.dist(v1, v2)

            if distance <= 10:
                break
            else:
                command += "forward " + str(int(math.ceil(0.7 * distance)))  # * 0.8
                # self.compose(command)

                # !! can I override the last command the bot got or not?
                # If *I can't*
                # then sleep(5)

        command += "forward " + str(int(math.ceil(distance)))
        # self.compose(command)

    # PART 1
    def receive_pass(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        # !! can make robot face goal, ball or own team plate initially, matters not
        (ball_coordinates, robot_coordinates, robot_dir_vector) = ((-320*0.46, 0), (50, 60), (1, 0))

        v1 = robot_coordinates
        v2 = ball_coordinates

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        # comms.compose(self.turn_command(turn))

        # !! maybe can wait a bit here
        # CHASE AND GET BALL FUNCTION

        print(command)
        # self.compose(command)

    # PART 2
    def receive_turn_pass(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        # !! can make robot face enemy plate or ball, matters not
        (ball_coordinates, robot_coordinates, robot_dir_vector) = ((-20, -40), (-320*0.46, 0), (1, 0))

        v1 = robot_coordinates
        v2 = ball_coordinates

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        # comms.compose(self.turn_command(turn))

        # !! maybe can wait a bit here
        # CHASE AND GET BALL FUNCTION

        (teammate_location, robot_coordinates, robot_dir_vector) = ((50, 60), (-320*0.46, 0), (1, -1))

        v1 = robot_coordinates
        v2 = teammate_coordinates

        turn = self.angle_a_to_b(v1, v2, robot_dir_vector)

        # !! Can confirm with camera?
        # !! Can ask camera or compass to confirm shit
        # comms.compose(self.turn_command(turn))

        # comms.compose("kick 100")


        print(command)
        # self.compose(command)

    # PART 3
    def intercept(self):
        # (ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        # !! can make robot face enemy plate or ball, matters not
        # !! plz correctly distinguish which enemy is which
        (ball_coordinates, other_bot, robot_coordinates) = ( (320*0.46,0), (-40,100), (40,-100), (1,0) )

        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (other_bot[1] - ball_coordinates[1]) / (other_bot[0] - ball_coordinates[0])

        # m = y - kx
        m = other_bot[1] - k * other_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x,y)

        get_to(i_location)


    def defend(self):
        #(ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)

        # !! this is simplest possible strategy
        # !! can change to robot seeking ball within confined defence area

        (enemy_bot, robot_coordinates) = ( (320*0.46,0), (-40,100), (40,-100), (1,0) )

        goal_center = (320*0.46,0)

        # Solving geometric problem with x,y axes for i_location
        # y = kx + m

        # k = (y2-y1) / (x2 - x1)
        k = (enemy_bot[1] - goal_center[1]) / (enemy_bot[0] - goal_center[0])

        # m = y - kx
        m = enemy_bot[1] - k * enemy_bot[0]

        x = robot_coordinates[0]
        y = k*x+m
        i_location = (x,y)

        get_to(i_location)

    # AUXILIARY functions
    def angle_between(self, p1, p2):
        ang1 = math.atan2(*p1[::-1])
        ang2 = math.atan2(*p2[::-1])
        return math.degrees((ang1 - ang2))

    def angle_a_to_b(self, r, b, dirv):
        d = (b[0] - r[0], b[1] - r[1])
        return self.angle_between(d, dirv)

    def dist(self, v1, v2):
        return math.hypot(v1[0] - v2[0], v1[1] - v2[1])

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


if __name__ == "__main__":
    pl = Planner()
    print("Test move and grab")
    pl.move_and_grab()
    print("Test rotate kick")
    pl.rotate_kick()
