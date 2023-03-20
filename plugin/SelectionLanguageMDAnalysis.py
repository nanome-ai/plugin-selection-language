import nanome
import os
from nanome.util import enums, Logs, async_callback
from nanome.api import ui
import MDAnalysis as mda
import tempfile

#TODO: Allow to run selection query for only one molecule
#TODO: Convert Nanome complex into MDAnalysis universe without writting to a PDB file
#TODO: Add a toggle to allow setting visibility when selecting

class SelectionLanguageMDAnalysis(nanome.AsyncPluginInstance):
    def start(self):
        self.toggle_visibility = False
        menu = self.menu
        menu.title = "Selection Language Input"
        menu.width = 0.9
        menu.height = 0.7

        top = menu.root.create_child_node()
        top.forward_dist = 0.001

        input_ln = top.create_child_node()

        self.input_text = input_ln.add_new_text_input("Input selection query")
        self.input_text.text_size = 0.5
        self.input_text.max_length = 1000
        self.input_text.horizontal_align = enums.HorizAlignOptions.Middle
        # self.input_text.register_submitted_callback(self.select_and_send)

        buttons_ln = top.create_child_node()
        buttons_ln.layout_orientation = nanome.ui.LayoutNode.LayoutTypes.horizontal.value

        btn_ln = buttons_ln.create_child_node()
        self.go_btn = btn_ln.add_new_button()
        self.go_btn.text.value.set_all("Select")
        self.go_btn.text.value.unusable = "Selecting..."
        self.go_btn.register_pressed_callback(self.select_and_send)
        self.go_btn.padding_type = nanome.ui.LayoutNode.PaddingTypes.fixed
        self.go_btn.padding_left = 0.3
        self.go_btn.padding_right = 0.3

        btn2_ln = buttons_ln.create_child_node()
        self.clear_btn = btn2_ln.add_new_button()
        self.clear_btn.text.value.set_all("Clear")
        self.clear_btn.register_pressed_callback(self.clear_selected_atoms)

        # btn3_ln = buttons_ln.create_child_node()
        # self.visi_tog = btn3_ln.add_new_toggle_switch("Set visibility")
        # self.visi_tog.register_pressed_callback(self.toggle_visi)
        # btn3_ln.sizing_type = nanome.ui.LayoutNode.SizingTypes.fixed.value
        # btn3_ln.sizing_value = 0.2

    def toggle_visi(self, togg):
        self.toggle_visibility = togg.selected

    def on_run(self):
        self.menu.enabled = True
        self.update_menu(self.menu)

    @async_callback
    async def select_and_send(self, selected_btn=None):
        text = self.input_text.input_text
        if len(text) == 0:
            Logs.error("Empty query")
            self.send_notification(
                enums.NotificationTypes.error,
                "Empty query, please input a selection query",
            )
            return

        if selected_btn is None:
            selected_btn = self.go_btn

        selected_btn.unusable = True

        Logs.debug("Receiving complexes")
        complex_indices = [comp.index for comp in await self.request_complex_list()]
        if len(complex_indices) == 0:
            Logs.error("No molecule loaded")
            self.send_notification(enums.NotificationTypes.error, "No molecule loaded")
            selected_btn.unusable = False
            return

        deep_complexes = await self.request_complexes(complex_indices)

        Logs.debug("Converting to MDAnalysis")

        self.mda_universes = self.convert_to_mda(deep_complexes)
        if self.mda_universes is None:
            Logs.error("Could not convert molecules to MDAnalysis molecules")
            self.plugin.send_notification(
                enums.NotificationTypes.error,
                "Could not convert molecules to MDAnalysis molecules",
            )
            selected_btn.unusable = False
            return

        Logs.debug("Converting to MDAnalysis done")

        # Do the actual selection
        count_selected = 0
        selections = []
        for u in self.mda_universes:
            try:
                sel = u.select_atoms(text)
            except Exception as e:
                Logs.error("Wrong selection query", e)
                self.send_notification(
                    enums.NotificationTypes.error, "Wrong selection query: " + str(e)
                )
                selected_btn.unusable = False
                return
            selections.append(sel)
            count_selected += len(sel)

        # Get selected atoms using indices
        for i in range(len(self.mda_universes)):
            if len(selections[i]) > 0:
                complex = deep_complexes[i]
                atoms = list(complex.atoms)
                for a in selections[i].atoms:
                    # Accessing Nanome atoms with mda selection atom indices
                    atoms[a.index].selected = True
                    if self.toggle_visibility:
                        atoms[a.index].set_visible(True)

        Logs.debug("Selecting {x} atoms".format(x=count_selected))
        self.update_structures_deep(deep_complexes)
        selected_btn.unusable = False

    @async_callback
    async def clear_selected_atoms(self, selected_btn=None):
        complex_indices = [comp.index for comp in await self.request_complex_list()]
        if len(complex_indices) == 0:
            Logs.error("No molecule loaded")
            self.send_notification(enums.NotificationTypes.error, "No molecule loaded")
            return
        deep_complexes = await self.request_complexes(complex_indices)

        for c in deep_complexes:
            for a in c.atoms:
                a.selected = False
        self.update_structures_deep(deep_complexes)

    # TODO: Ideally there is a way to convert Nanome complex to MDAnalysis molecule without writting to file
    def convert_to_mda(self, complexes):
        count = sum([len(list(c.atoms)) for c in complexes])
        if count == 0:
            return None
        universes = []
        for complex in complexes:
            to_mda_file = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
            complex.io.to_pdb(to_mda_file.name)
            u = mda.Universe(to_mda_file.name)
            universes.append(u)
            # os.remove(to_mda_file.name)

        # # Merge all molecules into a same universe
        # main_universe = universes[0]
        # for u in universes[1:]:
        #     main_universe = mda.Merge(main_universe.atoms, u.atoms)
        return universes


def main():
    plugin = nanome.Plugin(
        "Selection Language (MDAnalysis)",
        "Nanome plugin to input a selection query and select the corresponding atoms in Nanome",
        "Tools",
        False,
    )
    plugin.set_plugin_class(SelectionLanguageMDAnalysis)
    plugin.run()


if __name__ == "__main__":
    main()
