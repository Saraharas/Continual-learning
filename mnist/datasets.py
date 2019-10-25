class PermutedMnistGenerator():
    def __init__(self, max_iter=10, random_seed=0):
        # Open data file
        f = gzip.open('/mnist.pkl.gz', 'rb')
        train_set, valid_set, test_set = pickle.load(f, encoding='latin1')
        f.close()

        # Define train and test data
        self.X_train = np.vstack((train_set[0], valid_set[0]))
        self.Y_train = np.hstack((train_set[1], valid_set[1]))
        self.X_test = test_set[0]
        self.Y_test = test_set[1]
        self.random_seed = random_seed
        self.max_iter = max_iter
        self.cur_iter = 0

        self.out_dim = 10           # Total number of unique classes
        self.class_list = range(10) # List of unique classes being considered, in the order they appear

        # self.classes is the classes (with correct indices for training/testing) of interest at each task_id
        self.classes = []
        for iter in range(self.max_iter):
            self.classes.append(range(0,10))

        self.sets = self.classes

    def get_dims(self):
        # Get data input and output dimensions
        return self.X_train.shape[1], self.out_dim

    def next_task(self):
        if self.cur_iter >= self.max_iter:
            raise Exception('Number of tasks exceeded!')
        else:
            np.random.seed(self.cur_iter+self.random_seed)
            perm_inds = list(range(self.X_train.shape[1]))
            # First task is (unpermuted) MNIST, subsequent tasks are random permutations of pixels
            if self.cur_iter > 0:
                np.random.shuffle(perm_inds)

            # Retrieve train data
            next_x_train = deepcopy(self.X_train)
            next_x_train = next_x_train[:,perm_inds]

            # Initialise next_y_train to zeros, then change relevant entries to ones, and then stack
            #next_y_train = np.zeros((len(next_x_train), 10))
            #next_y_train[:,0:10] = np.eye(10)[self.Y_train]
            next_y_train = deepcopy(self.Y_train)
            # Retrieve test data
            next_x_test = deepcopy(self.X_test)
            next_x_test = next_x_test[:,perm_inds]

            #next_y_test = np.zeros((len(next_x_test), 10))
            #next_y_test[:,0:10] = np.eye(10)[self.Y_test]
            next_y_test = deepcopy(self.Y_test)
            self.cur_iter += 1

            return next_x_train, next_y_train, next_x_test, next_y_test

    def reset(self):
        self.cur_iter = 0
        
        
class SplitMnistGenerator():
    def __init__(self):
        # Open data file
        f = gzip.open('/mnist.pkl.gz', 'rb')
        train_set, valid_set, test_set = pickle.load(f, encoding='latin1')
        f.close()

        # Define train and test data
        self.X_train = np.vstack((train_set[0], valid_set[0]))
        self.X_test = test_set[0]
        self.train_label = np.hstack((train_set[1], valid_set[1]))
        self.test_label = test_set[1]

        # split MNIST
        task1 = [0, 1]
        task2 = [2, 3]
        task3 = [4, 5]
        task4 = [6, 7]
        task5 = [8, 9]
        self.sets = [task1, task2, task3, task4, task5]

        self.max_iter = len(self.sets)

        self.out_dim = 0        # Total number of unique classes
        self.class_list = []    # List of unique classes being considered, in the order they appear
        for task_id in range(self.max_iter):
            for class_index in range(len(self.sets[task_id])):
                if self.sets[task_id][class_index] not in self.class_list:
                    # Convert from MNIST digit numbers to class index number by using self.class_list.index(),
                    # which is done in self.classes
                    self.class_list.append(self.sets[task_id][class_index])
                    self.out_dim = self.out_dim + 1

        # self.classes is the classes (with correct indices for training/testing) of interest at each task_id
        self.classes = []
        for task_id in range(self.max_iter):
            class_idx = []
            for i in range(len(self.sets[task_id])):
                class_idx.append(self.class_list.index(self.sets[task_id][i]))
            self.classes.append(class_idx)

        self.cur_iter = 0

    def get_dims(self):
        # Get data input and output dimensions
        return self.X_train.shape[1], self.out_dim

    def next_task(self):
        if self.cur_iter >= self.max_iter:
            raise Exception('Number of tasks exceeded!')
        else:
            next_x_train = []
            next_y_train = []
            next_x_test = []
            next_y_test = []

            # Loop over all classes in current iteration
            for class_index in range(np.size(self.sets[self.cur_iter])):

                # Find the correct set of training inputs
                train_id = np.where(self.train_label == self.sets[self.cur_iter][class_index])[0]
                # Stack the training inputs
                if class_index == 0:
                    next_x_train = self.X_train[train_id]
                else:
                    next_x_train = np.vstack((next_x_train, self.X_train[train_id]))

                # Initialise next_y_train to zeros, then change relevant entries to ones, and then stack
                next_y_train_interm = np.zeros((len(train_id), self.out_dim))
                next_y_train_interm[:, self.classes[self.cur_iter][class_index]] = 1
                if class_index == 0:
                    next_y_train = next_y_train_interm
                else:
                    next_y_train = np.vstack((next_y_train, next_y_train_interm))
                next_y_train_vals = [np.where(r==1)[0][0] for r in next_y_train]
                
                # Repeat above process for test inputs
                test_id = np.where(self.test_label == self.sets[self.cur_iter][class_index])[0]
                if class_index == 0:
                    next_x_test = self.X_test[test_id]
                else:
                    next_x_test = np.vstack((next_x_test, self.X_test[test_id]))

                next_y_test_interm = np.zeros((len(test_id), self.out_dim))
                next_y_test_interm[:, self.classes[self.cur_iter][class_index]] = 1
                if class_index == 0:
                    next_y_test = next_y_test_interm
                else:
                    next_y_test = np.vstack((next_y_test, next_y_test_interm))
                next_y_test_vals = [np.where(r==1)[0][0] for r in next_y_test]

            self.cur_iter += 1

            return next_x_train, next_y_train_vals, next_x_test, next_y_test_vals

    def reset(self):
        self.cur_iter = 0