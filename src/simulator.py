"""
 BASED ON:
 Wireframe 3D cube simulation.
 Developed by Leonel Machava <leonelmachava@gmail.com>

 http://codeNtronix.com
"""
import pygame
import numpy as np
import time
import src.functions.rotation as rotation
from src.structures.thread import threatStructure

class Point3D:
    def __init__(self, x=0., y=0., z=0.):
        self.x, self.y, self.z = x, y, z

    def rotate_with_quaternion(self, q):
        v = rotation.multiply_vector_with_quaternion(np.array([self.x, self.y, self.z]), q)

        return Point3D(v[0], v[1], v[2])

    def project(self, win_width, win_height, fov, viewer_distance):
        """ Transforms this 3D point to 2D using a perspective projection. """
        factor = fov / (viewer_distance + self.z)
        x = self.x * factor + win_width / 2
        y = -self.y * factor + win_height / 2
        return Point3D(x, y, 1)

    def translate(self, tr):
        return Point3D(self.x + tr[0], self.y + tr[1], self.z + tr[2])


class simulator(threatStructure):
    
    def __init__(self, inputQueue, outputQueue, win_width=1280, win_height=960):
        
        super(simulator, self).__init__()
        self.target = self.run

        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.background_colour = (0, 0, 0)
        self.phone_frame_colour = (255, 255, 255)
        self.phone_colour = (0, 125, 125)
        self.phone_dimension = (1.2, 0.6, 0.18)
        self.phone_initial_position = (-5, -6, 1)

        # initialize pygame window
        pygame.init()
        self.screen = pygame.display.set_mode((win_width, win_height))
        pygame.display.set_caption("3D simulation of pedestrian dead reckoning (top view)")
        self.clock = pygame.time.Clock()

        # Compute phone coordinates (vertices) around local origin
        l, w, h = [x/2. for x in self.phone_dimension]
        self.vertices = [
            Point3D(-l, w, -h),
            Point3D(l, w, -h),
            Point3D(l, -w, -h),
            Point3D(-l, -w, -h),
            Point3D(-l, w, h),
            Point3D(l, w, h),
            Point3D(l, -w, h),
            Point3D(-l, -w, h)
        ]

        # Define the vertices that compose each of the 6 faces. Numbers are indices to the vertices list defined above.
        self.faces = [(0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6), (4, 0, 3, 7), (0, 4, 5, 1), (3, 2, 6, 7)]

        # initialize translation. The translation will be added to the changed orientation of the phone
        self.translate = list(self.phone_initial_position)

        # initialize track list
        self.track = [Point3D(self.translate[0],
                              self.translate[1],
                              self.translate[2]).project(self.screen.get_width(),
                                                         self.screen.get_height(),
                                                         256, 4)]
        # INITIAL SETUP
        # transform vertices using new quaternion
        t = self.transform_vertices(np.array([1,0,0,0]))

        # update the window
        self.screen.fill(self.background_colour)

        # print track of phone
        self.draw_trajectory()

        # print phone
        self.draw_phone(t)

    def run(self):
        """ Main Loop """
        while self.active:

            if len(self.inputQueue) != 0:
                dtp = self.inputQueue.dequeue()

                # last point
                if dtp == 'end':
                    time.sleep(1)
                    #input("Press Enter to continue...")
                    self.active = False
                    return

                # check if dtp is step and update core position (assume movement is in x-direction of phone)
                if dtp.isStep:

                    step_length = dtp.stepLength
                    step = rotation.multiply_vector_with_quaternion(np.array([step_length , 0,  0]), dtp.q_global)
                    # for now, remove the vertical component
                    step[2] = 0

                    # update translation
                    self.translate += step

                    # update track of core position
                    self.track.append(Point3D(self.translate[0],
                                              self.translate[1],
                                              self.translate[2]).project(self.screen.get_width(),
                                                                         self.screen.get_height(),
                                                                         256, 4))

                    # transform vertices using new quaternion
                    t = self.transform_vertices(dtp.q_global)

                    # update the window
                    self.screen.fill(self.background_colour)

                    # print track of phone
                    self.draw_trajectory()

                    # print phone
                    self.draw_phone(t)

                    # short break
                    time.sleep(0.05)
                self.outputQueue.enqueue(dtp)

    def transform_vertices(self, q):
        t = []
        # update vertices
        for v in self.vertices:
            # rotate the phone according to the quaternion
            r = v.rotate_with_quaternion(q)
            # translate the origin of the phone
            r = r.translate(self.translate)
            # transform the point from 3D to 2D
            p = r.project(self.screen.get_width(), self.screen.get_height(), 256, 4)
            # put the point in the list of transformed vertices
            t.append(p)
        return t

    def draw_trajectory(self):
        if len(self.track) > 1:
            for ii in range(1, len(self.track)):
                pnt1 = self.track[ii - 1]
                pnt2 = self.track[ii]
                pygame.draw.line(self.screen, (255, 0, 0), (pnt1.x, pnt1.y), (pnt2.x, pnt2.y))
        return

    def draw_phone(self, t):
        # print the structure of the phone
        for f in self.faces:
            pygame.draw.line(self.screen, self.phone_frame_colour, (t[f[0]].x, t[f[0]].y), (t[f[1]].x, t[f[1]].y))
            pygame.draw.line(self.screen, self.phone_frame_colour, (t[f[1]].x, t[f[1]].y), (t[f[2]].x, t[f[2]].y))
            pygame.draw.line(self.screen, self.phone_frame_colour, (t[f[2]].x, t[f[2]].y), (t[f[3]].x, t[f[3]].y))
            pygame.draw.line(self.screen, self.phone_frame_colour, (t[f[3]].x, t[f[3]].y), (t[f[0]].x, t[f[0]].y))

        # print the surface of the phone
        pointlist = [[t[self.faces[0][0]].x, t[self.faces[0][0]].y],
                     [t[self.faces[0][1]].x, t[self.faces[0][1]].y],
                     [t[self.faces[0][2]].x, t[self.faces[0][2]].y],
                     [t[self.faces[0][3]].x, t[self.faces[0][3]].y]]
        pygame.draw.polygon(self.screen,self.phone_colour, pointlist)

        # display the update window
        pygame.display.flip()

