import { Pipe, PipeTransform } from '@angular/core';

export const DAY_MAP: Record<number, string> = {
  0: $localize`:monday:Monday`,
  1: $localize`:tuesday:Tuesday`,
  2: $localize`:wednesday:Wednesday`,
  3: $localize`:thursday:Thursday`,
  4: $localize`:friday:Friday`,
  5: $localize`:saturday:Saturday`,
  6: $localize`:sunday:Sunday`
};

@Pipe({
  name: 'dayName'
})
export class DayNamePipe implements PipeTransform {

  transform(value: number): unknown {
    return DAY_MAP[value];
  }

}
