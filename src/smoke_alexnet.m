currentPath = fileparts(mfilename('fullpath'));
disp(currentPath);


% load images (each class in separate folders within a parent folder)
allImages = imageDatastore('/home/joey/Repos/Wildfire-Indicator/challenge1/training/', ...
    'IncludeSubfolders', true, ...
    'LabelSource', 'foldernames', ...
    'FileExtensions', '.jpg');
% Split data into training (80%) and test (20%) data sets
[trainingImages, testImages] = splitEachLabel(allImages, 0.8, 'randomize');
% Load Pre-trained Network (AlexNet)
% AlexNet is a pre-trained network trained on 1000 object categories.
% AlexNet is available as a support package on FileExchange.
alex = alexnet;
% Review Network Architecture
layers = alex.Layers;
% Modify Pre-trained Network
% AlexNet was trained to recognize 1000 classes, we need to modify it to
% recognize just 2 classes.
layers(23) = fullyConnectedLayer(2); % change this based on # of classes
layers(25) = classificationLayer;

% Perform Transfer Learning (can be adjusted)
opts = trainingOptions('sgdm', 'InitialLearnRate', 0.001, ...
'MaxEpochs', 50, 'MiniBatchSize', 64, 'ExecutionEnvironment', 'gpu');
% Set custom read function (this code is available in link)
trainingImages.ReadFcn = @readFunctionTrain; % resize
% Train the Network (may take 5 to 15+ minutes)
% Create a new network built on Alexnet w new layers
myNet = trainNetwork(trainingImages, layers, opts);
% Test Network Performance on Test Images
testImages.ReadFcn = @readFunctionTrain; % resize
predictedLabels = classify(myNet, testImages); % test

% Save the weights to a .mat file
save('smoke_model.mat', 'myNet');

%for i = 1:numel(testImages.Files)
%    img = readimage(testImages, i);
%   figure;
%    imshow(img);
%    fprintf("%d \n", i);
%    title(predictedLabels(i));
%end

accuracy = mean(predictedLabels == testImages.Labels);
fprintf("Accuracy %d", accuracy);