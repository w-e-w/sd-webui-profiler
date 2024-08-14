from modules import patches, script_callbacks, errors, shared, ui_components, scripts
from datetime import datetime
from functools import wraps
from pathlib import Path
import gradio as gr
import importlib


default_profile_functions = """# specify the functions that will be profiled
# example webui txt2img and img2img
modules.txt2img.txt2img
modules.img2img.img2img"""

all_profile_functions = []
trace_output = Path(scripts.basedir()) / 'traces'


def get_profile_functions():
    global all_profile_functions
    try:
        profile_functions = shared.opts.data.get('torch_profiler_wrapped_functions', default_profile_functions)
        all_profile_functions = [j for i in profile_functions.split('\n') if (j := i.strip()) and not j.startswith('#')]
        return all_profile_functions
    except Exception:
        all_profile_functions = default_profile_functions
        return default_profile_functions


def patch_functions():
    for function in all_profile_functions:
        enable_profiler(function)


get_profile_functions()

shared.options_templates.update(shared.options_section(('profiler_adv', 'Advance Profiler'), {
    'torch_profiler_enable': shared.OptionInfo(True, "Enable torch profiler"),
    'torch_profiler_wrapped_functions': shared.OptionInfo(
        default_profile_functions,
        'Profiler wrapper configs',
        gr.Textbox,
        {
            'lines': 5,
        },
        onchange=lambda: (get_profile_functions(), patch_functions())
    ).needs_restart(),
    'torch_profiler_disable_profiler': shared.OptionInfo(
        [],
        'Disable Profilers',
        ui_components.DropdownMulti,
        lambda: {
            'choices': get_profile_functions(),
        },
        refresh=get_profile_functions
    ),
    'torch_profiler_console_report_row_limit': shared.OptionInfo(10, f'console_report_row_limit', gr.Slider, {'minimum': -1, 'maximum': 100}).info('default 10; 0 disable; -1 unlimited'),
    'torch_profiler_extort_json': shared.OptionInfo(True, f'Export trace to json'),
}))


def torch_profiler_wrapper(func, full_name):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not shared.opts.torch_profiler_enable or full_name in shared.opts.torch_profiler_disable_profiler:
            return func(*args, **kwargs)

        from torch.profiler import profile, record_function, ProfilerActivity
        with profile(
                activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
                record_shapes=True,
                profile_memory=True,
                with_stack=True
        ) as prof:
            with record_function('model_inference'):
                res = func(*args, **kwargs)

        if shared.opts.torch_profiler_console_report_row_limit:
            print(prof.key_averages().table(sort_by='cpu_time_total', row_limit=shared.opts.torch_profiler_console_report_row_limit))
        if shared.opts.torch_profiler_extort_json:
            output_name = trace_output / full_name / f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            output_name.parent.mkdir(parents=True, exist_ok=True)
            prof.export_chrome_trace(str(output_name))
        return res

    return wrapper


def enable_profiler(module_name_function_name):
    try:
        module_name, _, function_name = module_name_function_name.rpartition('.')
        try:
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            patches.patch(__name__, module, function_name, torch_profiler_wrapper(function, full_name=f'{module_name}.{function_name}'))

            def undo_profiler():
                patches.undo(__name__, module, function_name)

            script_callbacks.on_script_unloaded(undo_profiler)
        except RuntimeError:
            pass

    except Exception:
        errors.report(f'Error enabling profiler for {module_name_function_name}', exc_info=True)


patch_functions()
