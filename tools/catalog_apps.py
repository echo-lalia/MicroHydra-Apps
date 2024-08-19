import yaml
import os



CWD = os.getcwd()
APP_SOURCE = os.path.join(CWD, 'app-source')



# load default app description
with open(os.path.join(APP_SOURCE, 'default.yml'), 'r', encoding="utf-8") as default_file:
    DEFAULT_DETAILS = yaml.safe_load(default_file.read())






def main():
    # load each directory in APP_SOURCE as an AppSource object
    app_sources = [AppSource(dir_entry) for dir_entry in os.scandir(APP_SOURCE) if dir_entry.is_dir()]
    
    for app in app_sources:
        app.make_readme()
    
    # update main README file with data from app_sources
    update_main_readme(app_sources)

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





def update_main_readme(app_sources):
    """
    This function reads all the apps provided in app_sources, and creates a main README.md file
    """
    # collect a set of all device names referenced by apps:
    all_devices = {device for app in app_sources for device in app.details['devices']}
    
    readme_text = """
<!---
This file is generated from automatically. (Any changes here will be overwritten)
--->
"""

    with open("README-header.md", "r", encoding="utf-8") as header_text:
        readme_text += header_text.read()
    
    readme_text += """

# Apps by device:  

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

"""
        for app in app_sources:
            if device in app.details['devices']:
                readme_text += f"""\
### [{app.name}]({app.url})  
> Author: **{app.author_string}** | License: **{app.license_string}** | Version: **{app.details['app_version']}**  
> {app.details['short_description']}
<br/>

"""
    
    with open("README.md", 'w', encoding="utf-8") as readme_file:
        readme_file.write(readme_text)



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
