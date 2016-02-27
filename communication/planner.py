import math
from math import *

# STATUS:
# - planner does correct calculations
# - plannere does optimal calculations
# - planner has been unit tested
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

        #self.compose(command)

    #rotate, move and grab
    def move_and_grab(self):

        #distance = 10
        #while(distance >=10):
        command = ""
        #(ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        (ball_coordinates, robot_coordinates, robot_dir_vector) = ( (0,0), (75,75), (0,-1) )
        print("expected turn - %d, expected dist - %d" % (-90, 226))

        v1 = robot_coordinates
        v2 = ball_coordinates

        turn = self.angle_a_to_b(v1,v2,robot_dir_vector)

        distance = self.dist(v1,v2)

        command += self.turn_command(turn) + " $"

        command += "forward " + str(int(math.ceil(0.9 * distance))) + " $" # * 0.8
        #self.compose(command)


        command += "open $"
        command += "forward " + str(int(math.ceil(0.1 * distance))) + " $"
        command += "stop"
        print(command)
        #self.compose(command)

    def rotate_kick(self):
        #(ball_coordinates, robot_coordinates, robot_dir_vector) = get_info(self.camera)
        (ball_coordinates, robot_coordinates, robot_dir_vector) = ( (160,160), (0,320*0.46), (0,1) )
        print("expected turn - %d?" % 45)

        v1 = robot_coordinates

        turn = self.angle_a_to_b(v1,(-320*0.46, 0.0),robot_dir_vector)

        command = ""

        command += self.turn_command(turn) + " $"

        command += "kick 100"
        print(command)
        #self.compose(command)



    def angle_between(self, p1, p2):
      ang1 = math.atan2(*p1[::-1])
      ang2 = math.atan2(*p2[::-1])
      return math.degrees((ang1 - ang2))
          
    def angle_a_to_b(self, r, b, dirv):
      d = (b[0] - r[0], b[1] - r[1])
      return self.angle_between(d, dirv)

    def dist(self, v1, v2):
        return  math.hypot(v1[0] - v2[0], v1[1] - v2[1])
    
    # Returns string "[left/right]  [turn degrees (<=180)]"
    def turn_command(self, turn):
      if turn <0:
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
