import yaml
import os
from PIL import Image
import json
import subprocess
import shutil
import datetime


MPY_VERSION = "6.3"


CWD = os.getcwd()
APP_SOURCE = os.path.join(CWD, 'app-source')



# load default app description
with open(os.path.join(APP_SOURCE, 'default.yml'), 'r', encoding="utf-8") as default_file:
    DEFAULT_DETAILS = yaml.safe_load(default_file.read())






def main():
    # load each directory in APP_SOURCE as an AppSource object
    app_sources = [AppSource(dir_entry) for dir_entry in os.scandir(APP_SOURCE) if dir_entry.is_dir()]

    # sort app_sources so that recently modified apps are first
    app_sources.sort(key=lambda app: app.mtime)

    # make each app-specific readme
    for app in app_sources:
        app.make_readme()

    # collect stats on apps (for readme file)
    stats = get_app_stats(app_sources)
    
    # update main README file with data from app_sources
    update_main_readme(app_sources, stats)

    # before making catalogs, clean old contents
    try:
        shutil.rmtree('catalog-output')
    except FileNotFoundError:
        pass # directory might not exist

    # compile apps into .mpy files
    if os.name == 'nt':
        print("WARNING: can't compile .mpy files on Windows.")
    else:
        compile_mpy_apps(app_sources)
    
    # zip apps to output folder for easy download from MicroHydra
    zip_apps(app_sources)

    # make a small catalog of apps for each device. 
    # (Designed to be easily downloaded/read from the device)
    make_device_catalogs(app_sources)






class AppSource:

    def __init__(self, dir_entry):
        self.dir_entry = dir_entry
        self.name = dir_entry.name

        self.details = DEFAULT_DETAILS.copy()

        # load app details if they exist:
        try:
            details_path = os.path.join(APP_SOURCE, self.name, 'details.yml')
            with open(details_path, 'r', encoding="utf-8") as detail_file:
                self.details.update(
                    yaml.safe_load(detail_file.read())
                )
        except FileNotFoundError:
            print(f"WARNING: App {self.name} has no details.yml")
        
        # clean device names by converting to lowercase
        self.details['devices'] = [name.lower() for name in self.details['devices']]

        # find app source url (for linking to app)
        self.url = self._get_app_url()

        # load app name (name of app in MicroHydra, might be different than folder name)
        self.app_name = self._get_app_name()

        self.author_string = self._make_author_string()

        self.license_string = self._make_license_string()

        self.icon_path = self._get_app_icon()

        self.mtime = self._get_modified_time()


    def _get_modified_time(self):
        """Ask git for the most recent commit timestamp in this app, convert to epoch."""
        # Inquire to git about latest commit
        output = subprocess.check_output(['git', 'log', '-1', r'--format="%ai"', self.dir_entry.path])

        # Convert bytes to str and clean it.
        output = output.decode().strip().strip('"')

        # convert to datetime
        dt = datetime.datetime.strptime(output, '%Y-%m-%d %H:%M:%S %z')

        # return epoch
        return dt.timestamp()
        



    def _get_app_icon(self):
        """
        Look for an app icon for this app. Store it in images/icons.
        Otherwise use default icon.
        """
        self_path = os.path.join(APP_SOURCE, self.name, self.app_name)

        # check for app icon:
        if os.path.isdir(self_path):
            for dir_entry in os.scandir(self_path):
                if dir_entry.name == "icon.raw":

                    # Extract this raw image to a transparent PNG for display.
                    with open(dir_entry, 'rb') as raw_icon:
                        img = Image.frombytes('1', (32,32), raw_icon.read())

                    palette = ((8, 0, 25, 0), (255, 243, 181, 255))
                    new_img = img.convert("RGBA")

                    for x_idx in range(32):
                        for y_idx in range(32):
                            src_val = 1 if img.getpixel((x_idx, y_idx)) else 0
                            new_img.putpixel((x_idx, y_idx), palette[src_val])

                    img_path = os.path.join("images", "icons", f"{self.name}.png")
                    new_img.save(img_path)
                    return img_path

        return os.path.join("images", "default_icon.png")



    def _get_app_url(self):
        url_base = "https://github.com/echo-lalia/MicroHydra-Apps/tree/main/app-source/"
        return url_base + self.name



    def _make_author_string(self):
        # make linked author string
        if self.details['author_link']:
            return f"[{self.details['author']}]({self.details['author_link']})"
        else:
            return self.details['author']


    def _make_license_string(self):
        # make linked/formatted license string
        if self.details['license']:
            if self.details['license_link']:
                return f"[{self.details['license']}]({self.details['license_link']})"
            return self.details['license']
        return "?"


    def _get_app_name(self):
        """Search for module folder or file in app folder"""
        for dir_entry in os.scandir(os.path.join(APP_SOURCE, self.name)):
            if dir_entry.is_dir():
                # if we found another directory inside our main directory,
                # it must be the module path
                return dir_entry.name
            elif dir_entry.name.endswith('.py'):
                # if this is a .py file, assume it must be a onefile app
                return dir_entry.name
                
    
            

    def __repr__(self):
        return f"AppSource({self.name})"


    def make_readme(self):
        """
        Generate README.md file for this app
        """

        # get an author icon (if we have the link)
        if self.details['author_link']:
            author_icon_string = f'<img src="{self.details["author_link"]}.png?size=26" width="13">'
        else:
            author_icon_string = ""

        # make a string to fetch the app icon.
        # we have to go 2 levels back before we can reach the images folder
        app_icon_string = f"../../{self.icon_path}"
    
        # assemble this app's README.md file
        readme = f"""\
<!---
This file is generated from the "details.yml" file. (Any changes here will be overwritten)
--->
# <img src="{app_icon_string}" width="16"> {self.name}
> ### {author_icon_string} **{self.author_string}**  
> Version: **{self.details['app_version']}** | License: **{self.license_string}**  
> App name: **{self.app_name.removesuffix(".py")}**
<br/>

{self.details['description']}

<br/><br/>

-----
### Installation:
{self.details['installation_instructions']}

"""     
        # finally, write that file
        with open(os.path.join(APP_SOURCE, self.name, 'README.md'), 'w', encoding="utf-8") as readme_file:
            readme_file.write(readme)





def update_main_readme(app_sources, stats):
    """
    This function reads all the apps provided in app_sources, and creates a main README.md file
    """
    # collect a set of all device names referenced by apps:
    all_devices = stats['all_devices']
    
    readme_text = """
<!---
This file is generated from automatically. (Any changes here will be overwritten)
--->
"""

    with open("README-header.md", "r", encoding="utf-8") as header_text:
        readme_text += header_text.read()
    
    readme_text += f"""

# Apps by device:  

*This repo currently hosts **{stats['num_apps']}** apps, for **{len(stats['all_devices'])}** unique devices, by **{stats['num_authors']}** different authors.*  
*Click a link below to jump to the apps for that specific device.*

"""
    # add links for apps by device:
    for device in all_devices:
        readme_text += f"- [{device.title()}](#{device})\n"
    

    # add apps by device:
    for device in sorted(all_devices):
        readme_text += f"""

<br/><br/><br/>        

## {device.title()}  
*There are {stats['device_count'][device]} apps for the {device.title()}.*


"""
        for app in app_sources:
            if device in app.details['devices']:

                # add author avatar to app listing
                if app.details['author_link']:
                    # github avatar can be found by adding '.png' to a profile link.
                    # icon will display at size "10", but using image size "20" looks better on highres displays.
                    author_icon_str = f'<img src="{app.details["author_link"]}.png?size=20" width="10">'
                else:
                    author_icon_str = ""

                # construct app listing
                readme_text += f"""\
### <img src="{app.icon_path}" width="14"> [{app.name}]({app.url})  
> {author_icon_str} **{app.author_string}**  
> Version: **{app.details['app_version']}** | License: **{app.license_string}**  
> {app.details['short_description']}
<br/>

"""
    
    with open("README.md", 'w', encoding="utf-8") as readme_file:
        readme_file.write(readme_text)



def get_app_stats(app_sources):
    """
    Count number of total apps, 
    apps by device, and unique authors.
    """
    app_stats = {'num_apps':len(app_sources), 'device_count':{}}
    
    # collect a set of all device names referenced by apps:
    all_devices = {device for app in app_sources for device in app.details['devices']}
    # count apps for each device
    for device in all_devices:
        apps_for_device = [app for app in app_sources if device in app.details['devices']]
        app_stats["device_count"][device] = len(apps_for_device)
    
    authors = {app.details['author'].lower() for app in app_sources}
    app_stats['num_authors'] = len(authors)
    app_stats['all_devices'] = all_devices

    return app_stats




def extract_file_data(dir_entry, path_dir):
    """Recursively extract DirEntry objects and relative paths for each file in directory."""
    if dir_entry.is_dir():
        output = []
        for r_entry in os.scandir(dir_entry):
            output += extract_file_data(r_entry, f"{path_dir}/{dir_entry.name}")
        return output
    else:
        return [(dir_entry, path_dir)]
    


def make_device_catalogs(app_sources):
    # make a small catalog of apps for each device. 
    # (Designed to be easily downloaded/read from the device)
    all_devices = {device for app in app_sources for device in app.details['devices']}
    
    
    for device in all_devices:
        device_catalog = {'mpy_version':MPY_VERSION}

        apps_for_device = [app for app in app_sources if device in app.details['devices']]
        for app in apps_for_device:
            device_catalog[app.name] = f"{app.details['short_description']} - {app.details['author']}"

        with open(os.path.join('catalog-output', f'{device.lower()}.json'), 'w') as catalog_file:
            catalog_file.write(
                json.dumps(device_catalog)
            )
    

def compile_mpy_apps(app_sources):
    # compile apps into .mpy files
    for app in app_sources:
        

        target_path = os.path.join(app.dir_entry, app.app_name)
        output_path = os.path.join(CWD, 'catalog-output', 'compiled', app.name)

        if os.path.isdir(target_path):
            app_files = []
            for dir_entry in os.scandir(target_path):
                app_files += extract_file_data(dir_entry, app.app_name)

            for dir_entry, relative_path in app_files:
                # Sometimes a slash appears and destroys os.path.join
                relative_path = relative_path.removeprefix('/')

                if dir_entry.name.endswith('.py'):
                    # compile py file to target folder
                    new_filename = dir_entry.name.removesuffix('.py') + '.mpy'

                    fileoutput = os.path.join(output_path, relative_path, new_filename)
                    mkdirs = os.path.join(output_path, relative_path)
                    
                    os.makedirs(mkdirs, exist_ok=True)
                    subprocess.run(["./tools/mpy-cross", "-o", fileoutput, dir_entry.path, "-march=xtensawin"])

                else:
                    # if not a .py file, just copy it over
                    mkdirs = os.path.join(output_path, relative_path)
                    os.makedirs(mkdirs, exist_ok=True)

                    fileoutput = os.path.join(output_path, relative_path, dir_entry.name)
                    shutil.copyfile(dir_entry, fileoutput)
        
        elif target_path.endswith('.py'):
            # if not a directory, target path should be a .py file, and should be compiled.
            new_filename = app.app_name.removesuffix('.py') + '.mpy'
            fileoutput = os.path.join(output_path, new_filename)

            os.makedirs(output_path, exist_ok=True)
            subprocess.run(["./tools/mpy-cross", "-o", fileoutput, target_path, "-march=xtensawin"])
        
        shutil.make_archive(output_path, 'zip', output_path)
        shutil.rmtree(output_path)




def zip_apps(app_sources):
    # zip apps to output folder for easy download from MicroHydra
    for app in app_sources:
        output_path = os.path.join(CWD, 'catalog-output', 'raw', app.name)

        shutil.make_archive(output_path, 'zip', root_dir=app.dir_entry, base_dir=app.app_name)




main()
