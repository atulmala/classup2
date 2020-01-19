import StringIO
import os

import pandas as pd
import numpy as np

import xlsxwriter
from django.http import HttpResponse
from google.cloud import storage

from rest_framework import generics

from formats.formats import Formats as format

from academics.models import Class
from setup.models import School


class GenerateAnalytics(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        school_id = request.query_params.get('school_id')
        school = School.objects.get(id=school_id)
        standard = request.query_params.get('standard')
        the_class = Class.objects.get(school=school, standard=standard)

        storage_client = storage.Client()
        bucket = storage_client.get_bucket('classup')

        master_data_file = '%s_%s_master_data.xlsx' % (str(school_id), the_class)
        file_path = 'classup2/Analytics/school/%s/%s' % (str(school_id), master_data_file)
        blob = bucket.blob(file_path)
        local_path = 'analytics/%s' % master_data_file
        blob.download_to_filename(local_path)

        analytics_file_name = 'class_%s_analytics.xlsx' % the_class
        output = StringIO.StringIO(analytics_file_name)
        analytics = xlsxwriter.Workbook(output)

        fmt = format()
        title_format = analytics.add_format(fmt.get_title())
        title_format.set_border()
        header = analytics.add_format(fmt.get_header())
        big_font = analytics.add_format(fmt.get_large_font())
        big_font.set_color('#33691E')
        medium_font = analytics.add_format(fmt.get_medium_fong())
        medium_font.set_color('#827717')
        section_heading = analytics.add_format(fmt.get_section_heading())
        section_heading.set_color('#4E342E')
        cell_bold = analytics.add_format(fmt.get_cell_bold())
        cell_bold.set_border()
        cell_normal = analytics.add_format(fmt.get_cell_normal())
        cell_normal.set_border()
        cell_left = analytics.add_format(fmt.get_cell_left())
        cell_left.set_border()
        perc_format = analytics.add_format(fmt.get_perc_format())
        big_perc_format = analytics.add_format(fmt.get_big_perc_format())
        perc_format.set_color('#37474F')

        sheets = ['Term I']
        for a_sheet in sheets:
            sheet = pd.read_excel(local_path, sheet_name=a_sheet, index_col=0)
            wb_sheet = analytics.add_worksheet(a_sheet)
            wb_sheet.set_landscape()
            wb_sheet.set_paper(9)  # A4 paper
            wb_sheet.fit_to_pages(1, 0)
            header_text = 'Analytics Sheet Class %s' % (the_class)
            wb_sheet.set_header('&L%s&RPage &P of &N' % header_text)
            wb_sheet.merge_range('A1:L1', '%s Analytics for class %s term: %s' % (school, the_class, a_sheet),
                                 title_format)
            student_df = sheet['Student']
            total_students = student_df.count()
            wb_sheet.set_column('C:C', 10)
            wb_sheet.set_column('D:D', 10)
            wb_sheet.set_column('E:E', 12)
            wb_sheet.set_column('F:F', 12)
            wb_sheet.set_column('G:G', 12)
            wb_sheet.set_column('H:H', 11)
            wb_sheet.set_column('I:I', 12)
            wb_sheet.set_column('J:J', 12)
            row = 1
            col = 3
            wb_sheet.write_string(row, col, 'Class', medium_font)
            col += 1
            wb_sheet.write_string(row, col, the_class.standard, big_font)
            col += 1
            wb_sheet.write_string(row, col, 'Students', medium_font)
            col += 1
            wb_sheet.write_number(row, col, total_students, big_font)
            col += 1

            sections_df = sheet['Section']
            sections = sections_df.unique()
            wb_sheet.write_string(row, col, 'Sections', medium_font)
            col += 1
            wb_sheet.write_number(row, col, sections_df.nunique(), big_font)

            # student section wise distribution analytics
            section_wise_students = sections_df.value_counts()
            student_in_section = []
            for section in sections:
                student_in_section.append(section_wise_students[section])

            row += 1
            col = 3
            categories = [a_sheet, row, col, row + sections_df.nunique() - 1, col]
            wb_sheet.write_column(row, col, sections, cell_bold)
            col += 1
            values = [a_sheet, row, col, row + sections_df.nunique() - 1, col]
            wb_sheet.write_column(row, col, student_in_section, cell_bold)
            chart = analytics.add_chart({'type': 'column'})
            chart.set_legend({'none': True})
            chart.set_y_axis({
                'visible': False,
                'major_gridlines': {'visible': False},
                'min': 0,
                'max': 50
            })
            chart.add_series({
                'categories': categories,
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#D1C4E9', '#311B92']},
                'data_labels': {'value': True},
            })
            chart.set_title({
                'name': 'Section wise Students',
                'name_font': {
                    'size': 14
                }
            })
            wb_sheet.insert_chart('D3', chart, {'x_offset': 0, 'y_offset': 0})

            # total marks analytics for all sections
            row = 20
            col = 2
            wb_sheet.merge_range(row, col, row, col + 2, 'Total Marks Analysis', section_heading)
            total_marks_df = sheet[['Student', 'Section', 'Total']]
            max_marks = 700.00
            row += 1
            wb_sheet.write_string(row, col, 'Highest', medium_font)
            col += 1
            highest = round(total_marks_df['Total'].max(), 2) / max_marks
            wb_sheet.write_number(row, col, highest, big_perc_format)
            col += 1
            wb_sheet.write_string(row, col, 'Average', medium_font)
            col += 1
            average = round(total_marks_df['Total'].mean(), 2) / max_marks
            wb_sheet.write_number(row, col, average, big_perc_format)
            col += 1
            wb_sheet.write_string(row, col, 'Min', medium_font)
            col += 1
            min = round(total_marks_df['Total'].min(), 2) / max_marks
            wb_sheet.write_number(row, col, min, big_perc_format)

            # analytics for each section separate - highest, average and min
            row += 1
            col = 3
            wb_sheet.write_string(row, col, 'Section', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Highest', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Average', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, 'Min', cell_bold)
            row += 1
            col = 3
            wb_sheet.write_column(row, col, sections, cell_bold)

            # as we have consolidated analytics for all sections readily available, insert it now
            row += sections_df.nunique()
            wb_sheet.write_string(row, col, 'All Sections', cell_bold)
            col += 1
            wb_sheet.write_number(row, col, highest, perc_format)
            col += 1
            wb_sheet.write_number(row, col, average, perc_format)
            col += 1
            wb_sheet.write_number(row, col, min, perc_format)

            # now, go to the top of this table to insert section specific analytics
            row -= sections_df.nunique()
            col = 4
            categories = [a_sheet, row, col - 1, row + sections_df.nunique(), col - 1]

            for section in sections:
                subset = total_marks_df['Section'] == section
                highest = round(total_marks_df[subset]['Total'].max() / max_marks, 2)
                wb_sheet.write_number(row, col, highest, perc_format)
                col += 1
                average = round(total_marks_df[subset]['Total'].mean() / max_marks, 2)
                wb_sheet.write_number(row, col, average, perc_format)
                col += 1
                min = round(total_marks_df[subset]['Total'].min() / max_marks, 2)
                wb_sheet.write_number(row, col, min, perc_format)
                row += 1
                col = 4
            chart = analytics.add_chart({'type': 'column'})
            chart.set_legend({'position': 'bottom'})
            chart.set_y_axis({
                'major_gridlines': {'visible': False},
                'min': 0,
                'max': 1
            })
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'categories': categories,
                'name': 'Highest',
                'values': values,
                'marker': {'type': 'automatic'},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                    }
                },
                'gradient': {'colors': ['#1B5E20', '#A5D6A7']},
                'overlap': 0,
            })
            col += 1
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'name': 'Average',
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#9E9D24', '#D4E157']},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                        'rotation': -90
                    }
                },
            })
            col += 1
            values = [a_sheet, row - sections_df.nunique(), col, row, col]
            chart.add_series({
                'name': 'Min',
                'values': values,
                'marker': {'type': 'automatic'},
                'gradient': {'colors': ['#D84315', '#FF8A65']},
                'data_labels': {
                    'value': True,
                    'font': {
                        'name': 'Consolas',
                        'size': 8,
                        'rotation': -90
                    }
                },
            })
            chart.set_title({
                'name': 'Section wise Total marks comparison',
                'name_font': {
                    'name': 'Calibri',
                    'color': 'blue',
                    'size': 14
                }
            })
            row = 31
            col = 0
            wb_sheet.insert_chart(row, col, chart, {'x_offset': 20, 'y_offset': 10})

            # show the names of top 5 students
            top_10 = total_marks_df.nlargest(10, ['Total'])
            row += 1
            col = 7
            wb_sheet.merge_range(row, col, row, col + 4, 'Top 10 students', header)
            row += 1
            wb_sheet.write_string(row, col, 'Rank', cell_bold)
            col += 1
            wb_sheet.merge_range(row, col, row, col + 1, 'Student', cell_bold)
            col += 2
            wb_sheet.write_string(row, col, 'Section', cell_bold)
            col += 1
            wb_sheet.write_string(row, col, '%', cell_bold)

            row += 1
            col = 7
            s_no = 1
            for idx in top_10.index:
                wb_sheet.write_number(row, col, s_no, cell_normal)
                s_no += 1
                col += 1
                wb_sheet.merge_range(row, col, row, col + 1, top_10['Student'][idx], cell_normal)
                col += 2
                wb_sheet.write_string(row, col, top_10['Section'][idx], cell_normal)
                col += 1
                wb_sheet.write_number(row, col, top_10['Total'][idx] / max_marks, perc_format)
                row += 1
                col = 7

            # student distribution in percentage segments (> 85, 85-70, 70-50, < 50)
            slabs = ['Above 85%', 'Between 85%-70%', 'Between 70%-50%', 'Below 50%']
            slab_values = []
            above_85 = total_marks_df[total_marks_df['Total'] > (max_marks * .85)]['Student'].count()
            print('above_85=%d' % above_85)
            slab_values.append(round(float(above_85) / float(total_students), 2))
            between_85_70 = total_marks_df[(total_marks_df['Total'] < (max_marks * .85)) & (total_marks_df['Total'] >
                                                                                            (max_marks * .70))][
                'Student'].count()
            print('between_85_70=%d' % between_85_70)
            slab_values.append(round(float(between_85_70) / float(total_students), 2))
            between_70_50 = total_marks_df[(total_marks_df['Total'] < (max_marks * .7)) & (total_marks_df['Total'] >
                                                                                           (max_marks * .50))][
                'Student'].count()
            print('between_70_50=%d' % between_70_50)
            slab_values.append(round(float(between_70_50) / float(total_students), 2))
            below_50 = total_marks_df[total_marks_df['Total'] < (max_marks * .5)]['Student'].count()
            print('below_50=%d' % below_50)
            slab_values.append(round(float(below_50) / float(total_students), 2))
            print(slab_values)

            row += 5
            col = 0
            wb_sheet.merge_range(row, col, row, col + 3, 'Total Marks Slab wise distribution', medium_font)
            col += 1
            row += 2
            wb_sheet.write_column(row, col, slabs)
            col += 1
            wb_sheet.write_column(row, col, slab_values, perc_format)

        os.remove(local_path)
        try:
            analytics.close()
        except Exception as e:
            print(e.message, type(e))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=%s' % analytics_file_name
        response.write(output.getvalue())
        return response
