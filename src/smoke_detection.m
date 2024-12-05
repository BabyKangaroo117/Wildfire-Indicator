% First verify the readFunctionTrain is available
if ~exist('readFunctionTrain', 'file')
    error('readFunctionTrain.m must be in your current directory or MATLAB path');
end

% Load the saved model
load('smoke_model.mat', 'myNet');

% Create figure window
fig = figure('Name', 'Real-time Smoke Detection', 'NumberTitle', 'off');

% Get current directory for saving frames
frameDir = pwd;
framePath = fullfile(frameDir, 'current_frame.jpg');

% Define GStreamer pipeline with tee to split the stream
gstCmd = sprintf(['gst-launch-1.0 -q v4l2src device=/dev/video0 ! tee name=t ! ', ...
    'queue ! jpegenc ! multifilesink location=%s t. ! ', ...
    'queue ! videoconvert ! autovideosink sync=false'], framePath);

% Initialize text object as empty
predictionText = [];
lastPredTime = tic;

try
    % Start the video pipeline in background
    [~, ~] = system([gstCmd ' &']);
    fprintf('Live video feed started. Close figure window to exit.\n');
    
    while isvalid(fig)
        % Only process predictions every 0.5 seconds
        if toc(lastPredTime) > 0.5
            try
                % Process the latest frame
                processedImg = readFunctionTrain(framePath);
                
                % Get prediction
                [prediction, scores] = classify(myNet, processedImg);
                confidence = max(scores) * 100;
                
                % Update console with prediction
                fprintf('Prediction: %s (%.1f%%)\n', char(prediction), confidence);
                
                lastPredTime = tic;
            catch ME
                % Ignore file read errors (expected when file is being written)
                if ~contains(ME.message, 'Unable to read file')
                    warning('Processing error: %s', ME.message);
                end
            end
        end
        
        pause(0.1);
        drawnow;
    end
    
catch ME
    fprintf('Error: %s\n', ME.message);
end

% Cleanup
if exist(framePath, 'file')
    delete(framePath);
end

% Kill the GStreamer pipeline
system('pkill -f "gst-launch.*video0"');
close(fig);