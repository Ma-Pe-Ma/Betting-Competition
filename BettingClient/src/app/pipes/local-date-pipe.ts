import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'localDate',
  pure: true
})
export class LocalDatePipe implements PipeTransform {

  transform(value: string | Date | null | undefined, timeZone: string, mode: 'date' | 'time' | 'datetime' | 'full' = 'datetime'): string {
    if (!value || '') {
      return '';
    }

    const date = typeof value === 'string' ? new Date(value) : value;

    let formatOptions: Intl.DateTimeFormatOptions;

    switch (mode) {
      case 'date':
        formatOptions = { year: 'numeric',month: '2-digit', day: '2-digit' };
        break;
      case 'time':
        formatOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit' };
        break;
      case 'datetime':
        formatOptions = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
        break;

      case 'full':
        formatOptions = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }
        break;
    }

    try {
      const options = { ...formatOptions, timeZone: timeZone };
      return new Intl.DateTimeFormat('hu-HU', options).format(date);
    } catch (err) {
      console.warn('Invalid timezone or dat e:', err);
      return '';
    }
  }

}
