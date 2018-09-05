import matplotlib.pyplot as plt


def create_plot(pdr):
    a_norm = []
    a_norm_smooth = []
    a_time = []
    step_a = []
    step_time = []
    for q in pdr.simulationQueue:
        a_time.append(q.time)
        a_norm.append(q.a_norm)
        a_norm_smooth.append(q.a_norm_smooth)
        if q.isStep:
            step_a.append(q.a_norm_smooth)
            step_time.append(q.time)

    fig, ax = plt.subplots(1, 1, figsize=(20, 5))
    plt.title('Stepcounting algorithm = ' + pdr.step_counter.algoName, fontsize=20)
    norm, = plt.plot(a_time, a_norm, label='acc_norm: raw data')
    smooth, = plt.plot(a_time, a_norm_smooth, label='acc_norm: smooth data')
    steps, = plt.plot(step_time, step_a, 'o', label='steps')
    plt.xlabel('time (ms)', fontsize=10)
    plt.ylabel('acc norm (m/s2', fontsize=10)

    plt.legend(handles=[norm, smooth, steps], fontsize=10)
    plt.show()
    print('steps / datapoints:', len(step_time), len(a_time))