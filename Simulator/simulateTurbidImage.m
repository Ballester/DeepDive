function T = simulateTurbidImage(input,Binf,c,dmap)

    % Set distance of the scene, for our experiment is always 0.58
    
    
    % Take just the luminance
    %[H S I ] = rgb2hsv(I);
    %[H S J ] = rgb2hsv(J);
    %Binf = double(rgb2gray(Binf))/255;    
%     
%     J = double(J);
%     I = double(I);
    

    
    

   % Binf estimation could not be done for now.
   
    % = sort(Binf(:,1))
    %BinfG = sort(Binf(:,2))
    %BinfB = sort(Binf(:,3))
    
    
        
    %Bvec = sort(Binf,'descend');  

    %Binf = mean(Bvec(1:15))
        
  %  Bvec = sort(Binf(:,2),'descend');  

  %  BinfG = mean(Bvec(1:15))
        
   % Bvec = sort(Binf(:,3),'descend'); 

 %   BinfB = mean(Bvec(1:15))


    
    
    % Still need to regulate
    
    % Estimate turbid noise


        
    
    
    %cR = estimateC(J,I,dmapInput,BinfR);
    %cR = 0.4;
    %cG = estimateC(J,I,dmapInput,BinfG);
    %cB = estimateC(J,I,dmapInput,BinfB);
    

    
%     dmapOutput = double(dmapOutput)./max(max(double(dmapOutput)));

     averageCossine = 0.75;
%     calculate the image with just the turbid noise
     

     TR = calculateTurbidImage(double(input(:,:,1))/255,c(1),dmap,averageCossine,Binf(1)); 
     averageCossine = 0.714;
     
     
     TG = calculateTurbidImage(double(input(:,:,2))/255,c(2),dmap,averageCossine,Binf(2)); 
%     
     averageCossine = 0.681;
     TB = calculateTurbidImage(double(input(:,:,3))/255,c(3),dmap,averageCossine,Binf(3)); 
%     
%     
     T(:,:,1) = TR;
     T(:,:,2) = TG;
     T(:,:,3) = TB;
     

end
