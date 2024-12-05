% Load the saved model
load('smoke_model.mat', 'myNet');

% Create video input object
cam = webcam(); % for default webcam
% Or specify a particular camera by index:
% cam = webcam(1);

% Create a figure window
figure('Name', 'Real-time Smoke Detection', 'NumberTitle', 'off');

% Initialize text for displaying prediction
predictionText = text(10, 10, '', 'Color', 'white', 'FontSize', 18);

try
    while true
        % Capture frame from camera
        img = snapshot(cam);
        
        % Preprocess image using the same function as training
        processedImg = readFunctionTrain(img);
        
        % Get prediction
        prediction = classify(myNet, processedImg);
        
        % Display the frame
        imshow(img);
        
        % Update prediction text
        predictionText.String = ['Prediction: ' char(prediction)];
        predictionText.Position = [10, 30]; % Adjust position if needed
        
        % Force display update
        drawnow;
        
        % Optional: Add delay to control processing speed
        pause(0.1);
        
        % Check if figure is still open
        if ~isvalid(predictionText.Parent)
            break;
        end
    end
catch ME
    % Clean up on error
    clear cam;
    rethrow(ME);
end

% Clean up
clear cam;
