## YOUTUBE CONTENT PRODUCTION

### INTRODUCTION

 This project have goal of automate mainly with **free resources** the production of **any youtube video** specially informative and **non-entertaiment** content, like courses, presentation, of motivation and reflexion videos

 We mainly are using **python** for access and automate main tasks with **FFMPEG** and other API calls and APIs usage 
 
 We are using **bash scripting** for general management and deployment of python modules
 
 And in some precise cases we are using **Node.js scripting** for some specific resources that we **can't manage with python**

 Most important feat for this project is build it with **0 budget**

### Introduction to our project architecture:
 In first place we was using a stage architecture, we basically separate everything in 1 directory and then we start adding modules and  directories

 Core change it's that now we have **layers of modules**, **stations for files**,**Core_data** and **deployment hall**

 Inside **layers** we got all related with python modules and **tasks** of production chain.

 Inside **stations** we got all related with **multimedia** required for processing inside production chain

 Inside **Core_data** we got **most_important_part** of our project, this is because here we'll store and manage **our data sets and prompt md and txt files for AI**.
 
### Layers of modules development:
 **In this project** layers are structured groups of python modules for **macro tasks** this tasks follow into micro tasks execution per module

##### Raw data extraction layer:
 Inside this layer we focus on extraction of every single python module that separate **Video, audio and transcription** per original video and required data for production chain as **data sets time stamps** .pkl and json files etc.

##### Content enhancement layer:
 Inside this layer, we'll manage every single python module that enhance **raw content quality**, like audio and video enhancement

##### Content redaction layer:
 Inside this layer. we'll manage every single python script releated with titles creation, description creation and hastags generation, 

##### Debugging layer strategy:
 We'll integrate a directory named **Debugging logs** that will contain all logs of execution, inside this directory we'll add python module that will use groq model for fast  analysis, exactly we'll compose a **General report** .txt file with this **Groq debugging python module**

##### Presentations generation layer:
 Inside here we'll build the modules that will use transcription and presentation requirements as parameters for build **HTML, CSS AND JS** pages that will work as **presentation in left side of video of where i'm talking**.

 In this same module we'll use pupetter for record and save presentation, presentation will be a static page with JS, HTML and CSS that use setIntervals generated for each timestamp of video and content of this

##### Mixing content layer:
 In this layer we'll mix every single python module that take tasks of mix audio with video, and then add subtitles+zoom with MoviePy 

 Then we'll add presentation as an overlay in video using moviePy

##### Content uploading layer:
 There we'll have all modules releated with **main youtube videos upload** and **youtube shorts uploading**

##### Backup layer strategy:
 We'll code some modules layer , using python modules for created absorb the tasks that main daily usage modules couldn't afford for **usage limits**, and we'll coordinate all this modules like this:
 
 **Quick fail log analysis** We'll use NVIDIA mainly for backups in **Code generation** and for other tasks we'll recay on github free models multi-accounts,

 **Layer modules approach** inside this backup layer we'll contain next python modules: **Code_generation-tasks-assistant, Redaction_content_generation-tasks-assistant, Multi-modal_generation-tasks-assistant** 

 Every single of this module will be present but not running initially in production chain, if we got a failure in middle of production for usage limits of one of our models we'll use this backups assitants 


### Stations for files:
 Inside this stations we'll have sub directories that will manage role of **filter using as reference type of file and flag in file name** for exclude, remove or check using **bash scripts inside every sub directory**  for example:

**-A .mp3 file that have _enhanced_ flag**
**-A .mp4 file that have _titleReady_ _descriptionReady_ _hashtagsReady_** 
**- A .mp4 file that have _subtitlesReady_ flag **
**- A .pkl or .json file that have _codeGeneration_ _shortExtraction_ _subtitlesIndexing_  **

###### 