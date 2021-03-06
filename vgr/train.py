from datasets import PermutedMnistGenerator, SplitMnistGenerator
from bnn import Bayes_Net, solver_train_predict
from gans import Fc_generator, Conv_generator
from gan_train import GAN_train, sample_noise_batch
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.utils.data as data_utils
from tqdm import tqdm
from IPython import display
code_size = 100
NTrainPointsMNIST = 60000
def train(dataset='permuted', n_tasks=5, batch_size=256, gan_epochs=301, solver_epochs=5):
    pred_accs = []
    if dataset == 'permuted':
        data_gen = PermutedMnistGenerator(max_iter=n_tasks, random_seed=0)
        gan = Fc_generator(code_size, 784)
    if dataset == 'split':
        data_gen = SplitMnistGenerator()
        gan = Conv_generator(code_size, 784)
    print('\n dataset generated, starting tasks')
    
    for task in tqdm(range(n_tasks)):
        
        #load task data
        x_new_train, y_new_train, x_new_test, y_new_test = data_gen.next_task()
        
        x_train = torch.Tensor(x_new_train)
        y_train = torch.Tensor(y_new_train)
        
        x_test = torch.Tensor(x_new_test)
        y_test = torch.Tensor(y_new_test)
        
        
        print('task {} data loaded'.format(task))
        if task !=0:
            print('running task {}'.format(task))
            #adding prev gans sampled data 
            for i in range(task):
                solver = Bayes_Net(lr=0.001, channels_in=1, side_in=784, hid_dim=100, 
                    cuda=torch.cuda.is_available(), classes=10, 
                    batch_size=batch_size, Nbatches=(NTrainPointsMNIST/batch_size))

                solver.model.load_state_dict(torch.load('vgr/stored_models/task_{}_solver_weights.pth'.format(task  -1)))
                solver.set_mode_train(False)
                
                
                gan.load_state_dict(torch.load('vgr/stored_models/task_{}_{}_gan_weights.pth'.format(task - 1, dataset)))
                gan.eval()
                
                x_gan_train = gan(sample_noise_batch(batch_size=batch_size, code_size=code_size))
                x_gan_test = gan(sample_noise_batch(batch_size=batch_size, code_size=code_size))                
                
                _, y_gan_train = solver.eval(x_gan_train, torch.zeros(len(x_gan_train)))
                _, y_gan_test = solver.eval(x_gan_test, torch.zeros(len(x_gan_test)))
                x_train = torch.cat([x_gan_train.detach().cpu(), x_train])
                y_train = torch.cat([y_gan_train.detach().cpu().type(torch.FloatTensor), y_train])
                x_test = torch.cat([x_gan_test.detach().cpu(), x_test])
                y_test = torch.cat([y_gan_test.detach().cpu().type(torch.FloatTensor), y_test])
            if dataset == 'permuted':
                task_b_size = batch_size * (task + 1)
            if dataset == 'split':
                task_b_size = batch_size
            train = data_utils.TensorDataset(x_train, y_train)
            train_loader = data_utils.DataLoader(train, batch_size=task_b_size, shuffle=True)
            test = data_utils.TensorDataset(x_test, y_test)
            test_loader = data_utils.DataLoader(test, batch_size=batch_size, shuffle=True)
        
            #train curr task Solver
            print('running solver task {}'.format(task))
            curr_solver, mean_pred_acc = solver_train_predict(batch_size=task_b_size, 
                                                               train_loader=train_loader, test_loader=test_loader, 
                                                               n_epochs=solver_epochs, seen_tasks=task)
            torch.save(curr_solver.model.state_dict(), 
                       'vgr/stored_models/task_{}_solver_weights.pth'.format(task))
            
            
            pred_accs.append(mean_pred_acc)
            
            #train curr task GAN
            print('running GAN task {}'.format(task))
            curr_generator = GAN_train(dataset=dataset, discr_input=784, discr_output=1, gen_input=code_size, gen_output=784, 
                                   batch_size=task_b_size, data_loader=train_loader, n_epochs=gan_epochs)
            
            torch.save(curr_generator.state_dict(), 
                       'vgr/stored_models/task_{}_{}_gan_weights.pth'.format(task, dataset))
            
            
        else:
            print('running task {}'.format(task))
            
            train = data_utils.TensorDataset(x_train, y_train)
            train_loader = data_utils.DataLoader(train, batch_size=batch_size, shuffle=True)
            test = data_utils.TensorDataset(x_test, y_test)
            test_loader = data_utils.DataLoader(test, batch_size=batch_size, shuffle=True)
        
            #train first Solver
            print('running solver task {}'.format(task))
            
            curr_solver, mean_pred_acc = solver_train_predict(batch_size=batch_size, 
                                                               train_loader=train_loader, 
                                                               test_loader=test_loader, 
                                                               n_epochs=solver_epochs, 
                                                               seen_tasks=task)
            torch.save(curr_solver.model.state_dict(), 
                       'vgr/stored_models/task_{}_solver_weights.pth'.format(task))
            
            
            pred_accs.append(mean_pred_acc)
            
            #train first GAN
            print('running GAN task {}'.format(task))
            curr_generator = GAN_train(dataset=dataset, discr_input=784, discr_output=1, gen_input=code_size, gen_output=784, 
                                   batch_size=batch_size, data_loader=train_loader, n_epochs=gan_epochs)
            torch.save(curr_generator.state_dict(), 
                       'vgr/stored_models/task_{}_{}_gan_weights.pth'.format(task, dataset))
            
        display.clear_output(True)
        print('pred_accs {}'.format(pred_accs))
        
        plt.title('VGR prediction accuracy')
        plt.xlabel('n_tasks')
        plt.ylabel('accuracy')
        plt.plot(pred_accs, 'b', marker='o')
        plt.ylim((0., 1.2))
        plt.xticks(np.arange(len(pred_accs)))
        plt.savefig('vgr/results/permuted_acc_plot{}_tasks.png'.format(task))
        plt.show()
        
        
