class Formats():
    def __init__(self):
        pass

    title = {
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter'
            }

    def get_title(self):
        return self.title

    header = {
                'bold': True,
                'bg_color': '#F7F7F7',
                'color': 'black',
                'align': 'center',
                'valign': 'top',
                'border': 1
            }

    def get_header(self):
        return self.header

    cell_normal = {
                'align': 'left',
                'valign': 'top',
                'text_wrap': True
            }

    def get_cell_normal(self):
        return self.cell_normal

    cell_bold = {
                'bold': True,
                'align': 'left',
                'valign': 'top',
                'text_wrap': True
            }

    def get_cell_bold(self):
        return self.cell_bold

    cell_component = {
                'bold': True,
                'color': 'gray',
                'align': 'left',
                'valign': 'top',
                'text_wrap': True
            }

    def get_cell_component(self):
        return self.cell_component

    cell_center = {
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'bold': True
            }

    def get_cell_center(self):
        return self.cell_center

    vertical_text = {
                'bold': True,
                'bg_color': '#F7F7F7',
                'align': 'center',
                'valign': 'vcenter',
                'rotation': 90
            }

    def get_vertical_text(self):
        return self.vertical_text

    perc_format = {
                'num_format': '0.0%',
                'font_size': 9,
                'align': 'center',
                'valign': 'vcenter',
                'bold': True,
                'border': 1
            }

    def get_perc_format(self):
        return self.perc_format

    cell_grade = {
                'align': 'center',
                'valign': 'vcenter',
                'bold': True,
                'border': 1
            }

    def get_cell_grade(self):
        return self.cell_grade

    cell_small = {
                'align': 'left',
                'valign': 'top',
                'font_size': 8,
                'bold': True,
                'border': 1,
                'text_wrap': True
            }

    def get_cell_small(self):
        return self.cell_small
