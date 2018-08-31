import numpy as np
import math

def angular_rate_to_quaternion_rotation(w, dt):
    # angular_rate_to_quaternion_rotation
    wx = w[0]
    wy = w[1]
    wz = w[2]

    l = (wx ** 2 + wy ** 2 + wz ** 2) ** 0.5

    if l != 0:
        dtlo2 = dt * l / 2

        q0 = math.cos(dtlo2)
        q1 = math.sin(dtlo2) * wx / l
        q2 = math.sin(dtlo2) * wy / l
        q3 = math.sin(dtlo2) * wz / l

        q = np.array([q0, q1, q2, q3])
    else:
        q = np.array([1, 0, 0, 0])

    return q

def angular_rate_to_rotation_matrix(w, dt):
    wx = w[0]
    wy = w[1]
    wz = w[2]

    l = (wx ** 2 + wy ** 2 + wz ** 2) ** 0.5

    if l != 0:
        dtlo2 = l * dt

        w_skew = np.cross(np.eye(3), w/l)

        # Rodrigues rotation formula:
        R = np.eye(3) + math.sin(dtlo2) * w_skew + (1 - math.cos(dtlo2)) * (np.dot(w_skew, w_skew) - np.eye(3))
    else:
        R = np.eye(3)

    return R

def quaternion_to_rotation_matrix(q):
    w = q[0]
    x = q[1]
    y = q[2]
    z = q[3]

    r11 = w * w + x * x - y * y - z * z
    r12 = 2 * (x * y - w * z)
    r13 = 2 * (x * z + w * y)
    r21 = 2 * (x * y + w * z)
    r22 = w * w - x * x + y * y - z * z
    r23 = 2 * (y * z - w * x)
    r31 = 2 * (x * z - w * y)
    r32 = 2 * (w * x + y * z)
    r33 = w * w - x * x - y * y + z * z

    R = np.array([[r11, r12, r13],
                 [r21, r22, r23],
                 [r31, r32, r33]])
    return R

def rotation_matrix_to_quaternion(R):
    """OWN INPUT. convert a rotation matrix to quaternion"""
    tr = R[0,0] + R[1,1] + R[2,2]

    if (tr > 0):
        S = math.sqrt(tr+1.0) * 2
        qw = 0.25 * S
        qx = (R[2,1] - R[1,2]) / S
        qy = (R[0,2] - R[2,0]) / S
        qz = (R[1,0] - R[0,1]) / S
    elif ((R[0,0] > R[1,1]) & (R[0,0] > R[2,2])):
        S = math.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
        qw = (R[2,1] - R[1,2]) / S
        qx = 0.25 * S
        qy = (R[0,1] + R[1,0]) / S
        qz = (R[0,2] + R[2,0]) / S
    elif (R[1,1] > R[2,2]):
        S = math.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
        qw = (R[0,2] - R[2,0]) / S
        qx = (R[0,1] + R[1,0]) / S
        qy = 0.25 * S
        qz = (R[1,2] + R[2,1]) / S
    else:
        S = math.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
        qw = (R[1,0] - R[0,1]) / S
        qx = (R[0,2] + R[2,0]) / S
        qy = (R[1,2] + R[2,1]) / S
        qz = 0.25 * S
    
    q = np.array([qw, qx, qy, qz])
    return q

def multiply_vector_with_quaternion(v, q):
    v_as_q = np.array([0, v[0], v[1], v[2]])
    q_t = np.array([q[0],-q[1],-q[2],-q[3]])

    v_as_q_new = quaternion_product(q, quaternion_product(v_as_q, q_t))

    v_new = v_as_q_new[1:]
    return v_new

def multiply_vector_with_rotation_matrix(v, R):
    v_new = R.dot(v)
    return v_new

def quaternion_to_roll_pitch_yaw(q):
    # Source: WIKIPEDIA
    w = q[0]
    x = q[1]
    y = q[2]
    z = q[3]

    ysqr = y * y

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    roll = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)

    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    yaw = math.atan2(t3, t4)

    rpy = np.array([roll, pitch, yaw])

    return rpy

def rotation_matrix_to_roll_pitch_yaw(R):

    if (R[0,0] != 0) and (R[2,2] != 0):

        roll = math.atan2(R[2,1],R[2,2])
        pitch = math.atan2(-R[2,0], math.sqrt(R[2,1] * R[2,1] + R[2,2] * R[2,2]))
        yaw = math.atan2(R[1,0],R[0,0])

        rpy = np.array([roll, pitch, yaw])

    else:
        rpy = quaternion_to_roll_pitch_yaw(rotation_matrix_to_quaternion(R))

    return rpy

def quaternion_product(p, q):
    """p, q are two quaternions; quaternion product."""
    r0 = p[0] * q[0] - p[1] * q[1] - p[2] * q[2] - p[3] * q[3]
    r1 = p[0] * q[1] + p[1] * q[0] + p[2] * q[3] - p[3] * q[2]
    r2 = p[0] * q[2] - p[1] * q[3] + p[2] * q[0] + p[3] * q[1]
    r3 = p[0] * q[3] + p[1] * q[2] - p[2] * q[1] + p[3] * q[0]

    qn = np.array([r0, r1, r2, r3])
    return qn
