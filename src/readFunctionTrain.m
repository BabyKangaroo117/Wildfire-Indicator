function I = readFunctionTrain(filename)
    try
        I = imread(filename, 'jpg');
        I = imresize(I, [227 227]);
    catch ME
        fprintf('Error with file: %s\n%s\n', filename, ME.message);
        rethrow(ME);
    end
end