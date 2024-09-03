
<!---
This file is generated from automatically. (Any changes here will be overwritten)
--->
<p align="center">
    <a href="https://github.com/echo-lalia/Cardputer-MicroHydra" alt="MicroHydra">
        <img src="https://img.shields.io/badge/MicroHydra-purple" /></a>
 &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/microhydra-frozen" alt="MicroHydra Firmware">
        <img src="https://img.shields.io/badge/Firmware-purple" /></a>
  &nbsp;&nbsp;
    <a href="https://github.com/echo-lalia/Cardputer-MicroHydra/wiki" alt="Wiki">
        <img src="https://img.shields.io/badge/Wiki-slateblue" /></a>
</p>

# MicroHydra Apps!
This is a companion repository with a collection of community made apps for MicroHydra. 

<br/>


## Adding your apps to this repository:
If you've made an app compatible with MicroHydra, you can add it to this repository by submitting a pull request.

> This repo automatically generates `README.md` files *(and more)* using the scripts under `/tools`.  
> For this to work, your app needs to be placed into the `app-source` directory, following the same general format as the apps around it.

*Here are step-by-step instructions for how you can add an app:*
- [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) this repository on your own account

- Add a directory specifically for your app to the `app-source` directory

- Place your app in that directory by uploading, or by adding your own repo as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules)  
  *(Either the `.py` file, or the entire folder containing your `__init__.py` should be added)*

- Create a `details.yml` file alongside your app. This should contain your name, a description, license, and specify the target device(s)  
  *(See [`app-source/default.yml`](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/app-source/default.yml), or the other uploaded apps for the format used here)*

- Submit a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to this repo with your changes.

<br/>

For clarity, this is how the `app-source` folder is structured:

*app-source/*    
├── ***myUniqueAppName/***  
│ &nbsp; &nbsp; &nbsp; ├── **myApp.py**  
│ &nbsp; &nbsp; &nbsp; └── **details.yml**  
│  
├── ***thisNameInRepo/***  
│ &nbsp; &nbsp; &nbsp; ├── ***thisNameInMicroHydra/***  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; ├── icon.raw  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; ├── someotherappfile.py  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; └── \_\_init\_\_.py    
│ &nbsp; &nbsp; &nbsp; └── **details.yml**  
│  
└── default.yml  



<br/><br/>


# Apps by device:  

*This repo currently hosts **15** apps, for **2** unique devices, by **6** different authors.*  
*Click a link below to jump to the apps for that specific device.*

- [Cardputer](#cardputer)
- [Tdeck](#tdeck)


<br/><br/><br/>        

## Cardputer  
*There are 15 apps for the Cardputer.*


### <img src="images/default_icon.png" width="14"> [HackSim](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/HackSim)  
>  **occulta1337**  
> Version: **1.0** | License: **?**  
> Simple Hack Simulation for MicroHydra
<br/>

### <img src="images/default_icon.png" width="14"> [Connect](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/Connect)  
> <img src="https://github.com/RealClearwave.png?size=20" width="10"> **[RealClearwave](https://github.com/RealClearwave)**  
> Version: **1.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> MicroHydra Connectivity Kit
<br/>

### <img src="images/icons/Music.png" width="14"> [Music](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/Music)  
> <img src="https://github.com/Benzamp.png?size=20" width="10"> **[Ben Harrison (Benzamp)](https://github.com/Benzamp)**  
> Version: **1.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A music player app.
<br/>

### <img src="images/icons/InfraRed.png" width="14"> [InfraRed](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/InfraRed)  
> <img src="https://github.com/ndrnmnk.png?size=20" width="10"> **[ndrnmnk](https://github.com/ndrnmnk)**  
> Version: **1.0** | License: **?**  
> Infrared codes sender/reciever app.
<br/>

### <img src="images/icons/tinyknight.png" width="14"> [tinyknight](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/tinyknight)  
> <img src="https://github.com/foopod.png?size=20" width="10"> **[foopod](https://github.com/foopod)**  
> Version: **1.0** | License: **?**  
> A game by Jono Shields
<br/>

### <img src="images/default_icon.png" width="14"> [mmlPlay](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/mmlPlay)  
> <img src="https://github.com/RealClearwave.png?size=20" width="10"> **[RealClearwave](https://github.com/RealClearwave)**  
> Version: **1.1** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Music Macro Language player
<br/>

### <img src="images/default_icon.png" width="14"> [LowPowerClock](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/LowPowerClock)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **1.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Another simple clock app.
<br/>

### <img src="images/default_icon.png" width="14"> [MHBasic](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/MHBasic)  
> <img src="https://github.com/RealClearwave.png?size=20" width="10"> **[RealClearwave](https://github.com/RealClearwave)**  
> Version: **1.1** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A BASIC interpreter and REPL
<br/>

### <img src="images/default_icon.png" width="14"> [KanjiReader](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/KanjiReader)  
> <img src="https://github.com/RealClearwave.png?size=20" width="10"> **[RealClearwave](https://github.com/RealClearwave)**  
> Version: **1.1** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A reader that can display kanji.
<br/>

### <img src="images/default_icon.png" width="14"> [timer](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/timer)  
> <img src="https://github.com/foopod.png?size=20" width="10"> **[foopod](https://github.com/foopod)**  
> Version: **1.0** | License: **?**  
> A kitchen timer app.
<br/>

### <img src="images/default_icon.png" width="14"> [Wikipedia](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/Wikipedia)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Fetch Wikipedia article summaries
<br/>

### <img src="images/icons/GameOfLife.png" width="14"> [GameOfLife](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/GameOfLife)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Conway's Game of Life
<br/>

### <img src="images/default_icon.png" width="14"> [flappyStamp](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/flappyStamp)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A simple game for the Cardputer
<br/>

### <img src="images/default_icon.png" width="14"> [chaosDice](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/chaosDice)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A dice rolling app
<br/>

### <img src="images/default_icon.png" width="14"> [FancyClock](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/FancyClock)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **1.2** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A clock app
<br/>



<br/><br/><br/>        

## Tdeck  
*There are 4 apps for the Tdeck.*


### <img src="images/default_icon.png" width="14"> [Wikipedia](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/Wikipedia)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Fetch Wikipedia article summaries
<br/>

### <img src="images/icons/GameOfLife.png" width="14"> [GameOfLife](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/GameOfLife)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> Conway's Game of Life
<br/>

### <img src="images/default_icon.png" width="14"> [chaosDice](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/chaosDice)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **2.0** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A dice rolling app
<br/>

### <img src="images/default_icon.png" width="14"> [FancyClock](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/FancyClock)  
> <img src="https://github.com/echo-lalia.png?size=20" width="10"> **[echo-lalia](https://github.com/echo-lalia)**  
> Version: **1.2** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)**  
> A clock app
<br/>

