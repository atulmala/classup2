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
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            }

    def get_cell_normal(self):
        return self.cell_normal

    cell_right_border = {
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'border': 1,
        'right': 6,
        'text_wrap': True
    }

    def get_cell_right_border(self):
        return self.cell_right_border

    cell_bold = {
                'bold': True,
                'align': 'left',
                'valign': 'vcenter',
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

    cell_total = {
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
                'bold': True,
                'border': 1
            }

    def get_cell_total(self):
        return self.cell_total

    cell_left = {
        'align': 'left',
        'valign': 'vcenter'
        }

    def get_cell_left(self):
        return self.cell_left

    vertical_text = {
                'font_size': 8,
                'bold': True,
                'bg_color': '#F7F7F7',
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True,
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

    cell_grade2 = {
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'border': 1
    }

    def get_cell_grade2(self):
        return self.cell_grade2

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

    present_format = {
        'align': 'center',
        'valign': 'vcenter',
        'font_color': 'green'
        }

    def get_present_format(self):
        return self.present_format

    absent_format = {
        'align': 'center',
        'valign': 'vcenter',
        'font_color': '#FF0000'
        }

    def get_absent_format(self):
        return self.absent_format

    holiday_format = {
        'align': 'center',
        'valign': 'vcenter',
        'font_color': 'blue'
    }

    def get_holiday_format(self):
        return self.holiday_format

    bold_italics = {
        'align': 'center',
        'font_size': 11,
        'bold': True,
        'italic': True
    }

    def get_bold_italics(self):
        return self.bold_italics
