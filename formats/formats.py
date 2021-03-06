class Formats():
    def __init__(self):
        pass

    comments = {
        'text_wrap': True,
        'valign': 'top',
        'border': 1
    }

    def get_comments(self):
        return self.comments

    large_font = {
        'bold': True,
        'font_size': 34,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    }

    def get_large_font(self):
        return self.large_font

    medium_font = {
        'bold': True,
        'font_size': 18,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    }

    def get_medium_fong(self):
        return self.medium_font

    section_heading = {
        'bold': True,
        'italic': True,
        'font_size': 18,
        'text_wrap': True
    }

    def get_section_heading(self):
        return self.section_heading

    title = {
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    }

    def get_title(self):
        return self.title

    header = {
        'bold': True,
        'bg_color': '#F7F7F7',
        'color': 'black',
        'align': 'center',
        'valign': 'top',
        'border': 1,
        'text_wrap': True
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
        'valign': 'vcenter',
        'text_wrap': True
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

    big_perc_format = {
        'num_format': '0.0%',
        'font_size': 22,
        'align': 'center',
        'valign': 'vcenter',
        'bold': True,
        'border': 0
    }

    def get_big_perc_format(self):
        return self.big_perc_format

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

    cell_green = {
        'align': 'left',
        'valign': 'top',
        'font_size': 8,
        'font_color': '#1B5E20',
        'bold': True,
        'border': 1,
        'text_wrap': True
    }

    def get_cell_green(self):
        return self.cell_green

    cell_red = {
        'align': 'left',
        'valign': 'top',
        'font_size': 8,
        'font_color': '#E53935',
        'bold': True,
        'border': 1,
        'text_wrap': True
    }

    def get_cell_red(self):
        return self.cell_red

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
        'valign': 'vcenter',
        'font_size': 11,
        'bold': True,
        'italic': True
    }

    def get_bold_italics(self):
        return self.bold_italics

    rank_format = {
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 14,
        'border': 1,
        'bold': True,
        'italic': True
    }

    def get_rank_format(self):
        return self.rank_format

    colors = [
        '#C62828', '#6A1B9A', '#880E4F', '#311B92', '#1A237E', '#2962FF',
        '#1B5E20', '#33691E', '#3E2723', '#263238', '#4E342E', '#004D40'
    ]

    def get_colors(self):
        return self.colors
