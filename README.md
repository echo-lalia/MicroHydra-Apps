
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

app-source/    
├── myUniqueAppName/  
│ &nbsp; &nbsp; &nbsp; ├── myApp.py  
│ &nbsp; &nbsp; &nbsp; └── details.yml  
│  
├── thisNameInRepo/  
│ &nbsp; &nbsp; &nbsp; ├── thisNameInMicroHydra/  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; ├── icon.raw  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; ├── someotherappfile.py  
│ &nbsp; &nbsp; &nbsp; │ &nbsp; &nbsp; &nbsp; └── \_\_init\_\_.py  
│ &nbsp; &nbsp; &nbsp; └── details.yml  
│  
└── default.yml  



<br/><br/>


# Apps by device:  

*This repo currently hosts **14** apps, for **1** unique devices, by **4** different authors.*  
*Click a link below to jump to the apps for that specific device.*

- [Cardputer](#cardputer)

<br/><br/>


## Cardputer  
*There are 14 apps for the Cardputer.*


### <img src="images\default_icon.png" width="14"> [AppStore](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/AppStore)  
> Author: **[RealClearwave](https://github.com/RealClearwave)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A Simple AppStore for downloading from Github
<br/>

### <img src="images\default_icon.png" width="14"> [chaosDice](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/chaosDice)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A dice rolling app
<br/>

### <img src="images\default_icon.png" width="14"> [FancyClock](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/FancyClock)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.1**  
> A clock app
<br/>

### <img src="images\default_icon.png" width="14"> [flappyStamp](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/flappyStamp)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A simple game for the Cardputer
<br/>

### <img src="images\icons\GameOfLife.png" width="14"> [GameOfLife](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/GameOfLife)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> Conway's Game of Life
<br/>

### <img src="images\default_icon.png" width="14"> [InfraRed](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/InfraRed)  
> Author: **[ndrnmnk](https://github.com/ndrnmnk)** | License: **?** | Version: **1.0**  
> Infrared codes app.
<br/>

### <img src="images\default_icon.png" width="14"> [KanjiReader](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/KanjiReader)  
> Author: **[RealClearwave](https://github.com/RealClearwave)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A reader that can display kanji.
<br/>

### <img src="images\default_icon.png" width="14"> [LowPowerClock](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/LowPowerClock)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> Another simple clock app.
<br/>

### <img src="images\default_icon.png" width="14"> [MHBasic](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/MHBasic)  
> Author: **[RealClearwave](https://github.com/RealClearwave)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A BASIC interpreter and REPL
<br/>

### <img src="images\default_icon.png" width="14"> [mmlPlay](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/mmlPlay)  
> Author: **[RealClearwave](https://github.com/RealClearwave)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> Music Macro Language player
<br/>

### <img src="images\default_icon.png" width="14"> [timer](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/timer)  
> Author: **[foopod](https://github.com/foopod)** | License: **?** | Version: **1.0**  
> A kitchen timer app.
<br/>

### <img src="images\icons\tinyknight.png" width="14"> [tinyknight](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/tinyknight)  
> Author: **[foopod](https://github.com/foopod)** | License: **?** | Version: **1.0**  
> A game by Jono Shields
<br/>

### <img src="images\default_icon.png" width="14"> [wavPlay](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/wavPlay)  
> Author: **[RealClearwave](https://github.com/RealClearwave)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.0**  
> A Wave player.
<br/>

### <img src="images\default_icon.png" width="14"> [Wikipedia](https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/Wikipedia)  
> Author: **[echo-lalia](https://github.com/echo-lalia)** | License: **[MIT](https://github.com/echo-lalia/MicroHydra-Apps/blob/main/LICENSE)** | Version: **1.2**  
> Fetch Wikipedia article summaries
<br/>

