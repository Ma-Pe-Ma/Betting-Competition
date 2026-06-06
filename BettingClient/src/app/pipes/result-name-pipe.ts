import { Pipe, PipeTransform } from '@angular/core';

export const RESULTNAME_MAP: Record<number, string> = {
  0: $localize`:@@t1:Champion`,
  1: $localize`:@@t2:Finalist`,
  2: $localize`:@@t4:Semi-finals`,
  3: $localize`:@@t8:Quarter-finals`,
  4: $localize`:@@t16:Round of 16`,
};

@Pipe({
  name: 'resultName'
})
export class ResultNamePipe implements PipeTransform {

  transform(value: number): string {
    return RESULTNAME_MAP[value];
  }
}
