# MicroHydra Apps!
This is a companion repository with a collection of apps for MicroHydra. 

<br/>


## Adding your apps to this repository:
If you've made an app compatible with MicroHydra for the M5Stack Cardputer, you can add it to this repository using the Pull requests feature.


<br/>

Create a personal fork for your additions, and upload your apps to the apps folder. 

If your app needs any additional modules (and if this is allowed by the licenses for those modules) then you can upload those as well.   

For compatibility and user-friendliness, if there are any additional app-specific files needed to run your app, I encourage you to place those in a dedicated folder inside the apps folder, with a folder name matching the name of your app, this way, if someone wants to install your app, they can just drag and drop the file and folder onto their device.    
*(of course, your apps will need to be setup to import the required files from that folder, for this to work.)*

This isn't a hard rule though; it might just make more sense to have a different directory for some apps. For example, if you made an app to view pictures stored on the device, you would probably feel it made more sense to keep those files in some kind of "pictures" folder in the root directory, instead of in the app folder. Use your own judgement here. 

<br/>

Once your app is uploaded, you can add a little description of it (and credit yourself!) here in README.md.   
Make sure to also give any additional instructions that are needed for installing your app, and credit any other authors who's code you're uploading.


<br/>
<br/>
<br/>

# Apps:
<br/>

### FancyClock
Author: echo-lalia | MIT License | Version: 1.1

This is a simple clock app that you can run when you just want something on your cardputer's display. It displays the time, date, and battery level, and bounces around the screen, leaving a colorful, somewhat 3d-looking trail behind it.

-----

<br/>

### Wikipedia
Author: echo-lalia | MIT License | Version: 1.2

This is a straightforward app which uses the wifi config set in MicroHydra, to connect to a wifi network, and fetch the summary of a Wikipedia article. 

-----

<br/>

### tinyKnight
Author: [foopod](https://github.com/foopod)

A cute little endless runner game for the Cardputer, by Jono Shields

-----

<br/>

### FlappyStamp
Author: echo-lalia | MIT License | Version: 1.0

A simple game concept redesigned for the cardputer. Play as the M5Stamp and dodge pillars of PCBs; try to beat your high score!

-----

<br/>

### timer
Author: [foopod](https://github.com/foopod)

A kitchen timer app, by Jono Shields

-----

<br/>

### chaosDice
Author: echo-lalia | MIT License | Version: 1.0

This dice app lets you roll a digital die (2,4,6,8,10,12,20, or 100 sides).   
The app uses the built in ADC's to generate a long random seed (which is displayed as an animation when you roll) and uses some simple math to convert it into a true random number within your chosen die range. Results have been tested casually (500000 rolls visualized in a histogram, for each die type) and the rolls appear to be pretty uniform in distribution. 

-----

<br/>
