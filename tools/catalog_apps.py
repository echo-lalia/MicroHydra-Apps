import yaml
import os
from PIL import Image



CWD = os.getcwd()
APP_SOURCE = os.path.join(CWD, 'app-source')



# load default app description
with open(os.path.join(APP_SOURCE, 'default.yml'), 'r', encoding="utf-8") as default_file:
    DEFAULT_DETAILS = yaml.safe_load(default_file.read())






def main():
    # load each directory in APP_SOURCE as an AppSource object
    app_sources = [AppSource(dir_entry) for dir_entry in os.scandir(APP_SOURCE) if dir_entry.is_dir()]

    # make each app-specific readme
    for app in app_sources:
        app.make_readme()

    # collect stats on apps (for readme file)
    stats = get_app_stats(app_sources)

    
    
    # update main README file with data from app_sources
    update_main_readme(app_sources, stats)

    # make a small catalog of apps for each device. 
    # (Designed to be easily downloaded/read from the device)
    make_device_catalogs()

    # compile apps into .mpy files
    compile_mpy_apps()
    
    # zip apps to output folder for easy download from MicroHydra
    zip_apps()






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

        # assemble this app's README.md file
        readme = f"""\
<!---
This file is generated from the "details.yml" file. (Any changes here will be overwritten)
--->
# {self.name}
> Author: **{self.author_string}** | License: **{self.license_string}** | Version: **{self.details['app_version']}**  
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
    
    readme_text += """
<br/><br/>

"""

    # add apps by device:
    for device in all_devices:
        readme_text += f"""
## {device.title()}  
*There are {stats['device_count'][device]} apps for the {device.title()}.*


"""
        for app in app_sources:
            if device in app.details['devices']:
                readme_text += f"""\
### <img src="{app.icon_path}" width="14"> [{app.name}]({app.url})  
> Author: **{app.author_string}** | License: **{app.license_string}** | Version: **{app.details['app_version']}**  
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






def make_device_catalogs():
    # update main README file with data from app_sources
    pass
    

def compile_mpy_apps():
    # compile apps into .mpy files
    pass


def zip_apps():
    # zip apps to output folder for easy download from MicroHydra
    pass




main()
