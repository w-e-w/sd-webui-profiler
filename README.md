# sd-webui-profiler

this is a tool for profiling stable diffusion webui
this extension creates a wrapper function that it developer can use to wish profile
the developer can specify the path to the function inside the UI and without any modification there code to enable profileing

since a [profiler was recently added to the base webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui/commit/57e6d05a43e4bdf4575e520f1a04c17e80fe58cc) most likely this essential will be no longer developed

### Usage
Settings > Profiler

- Profile wrapped functions

- specify the function they wish to profile and the profiler rapper will be applied to function

```py
# specify the functions that will be profiled
# example webui txt2img and img2img
modules.txt2img.txt2img
modules.img2img.img2img
```

the above config will wrap profiler around the function use for image generation in webui  

- Enable torch profiler
this acts as a global toggle for enabling or disabling the profiling
- Disable Profilers
for disabling specific profilers
- console_report_row_limit
controls how many lines of table will be print to the console
- Export trace to json
controls whether the result is exported to json