## YOUTUBE CONTENT PRODUCTION

### INTRODUCTION

 This project have goal of automate mainly with **free resources** the production of **any youtube video** specially informative and **non-entertaiment** content, like courses, presentation, of motivation and reflexion videos

 We mainly are using **python** for access and automate main tasks with **FFMPEG** and other API calls and APIs usage 
 
 We are using **bash scripting** for general management and deployment of python modules
 
 And in some precise cases we are using **Node.js scripting** for some specific resources that we **can't manage with python**


### Layers of development:

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
 

##### Backup layer strategy:
 We'll code some modules layer , using python modules for created absorb the tasks that main daily usage modules couldn't afford for **usage limits**, and we'll coordinate all this modules like this:
 
 **Quick fail log analysis** We'll use NVIDIA mainly for backups in **Code generation** and for other tasks we'll recay on github free models multi-accounts,

 **Layer modules approach** inside this backup layer we'll contain next python modules: **Code_generation-tasks-assistant, Redaction_content_generation-tasks-assistant, Multi-modal_generation-tasks-assistant** 

 Every single of this module will be present but not running initially in production chain, if we got a failure in middle of production for usage limits of one of our models we'll use this backups assitants 
