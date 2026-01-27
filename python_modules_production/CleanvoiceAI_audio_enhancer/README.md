
## INTRODUCTION 

 In this module we got the task in the work flow of get the separated audio in our directory with porpoise of retain the **base audio** for raw video, for this we relay in *2 main tools* **CleanVoiceAI and file.io** for first upload our raw video to a place where we can uploaded to our CleanVoiceAI, there it will be enhanced and then downloaded and moved in the next Directory that will be used to mix audio with video

 Script runs using API key from CleanVoiceAI and free API from file.io
  

### Script structure

We relay in our main class named **CleanVoiceEnhancer** were we define as main properties our **input directory** where we get our raw audio and our **output directory** where we'll get our **enhanced audio**  

 ```python
     DEFAULT_INPUT_DIR = Path("../../Pre_production_content/audios")
    DEFAULT_OUTPUT_DIR = Path("../../in_production_content/enhanced_audios")
    BASE_URL = "https://api.cleanvoice.ai/v2"                      
    FILEIO_URL = "https://file.io"                                 

 ```

It's very important define our properties as a **Path** because we'll use it for interact with directories for our local environment

