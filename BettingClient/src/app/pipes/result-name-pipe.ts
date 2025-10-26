import { Pipe, PipeTransform } from '@angular/core';

export const RESULTNAME_MAP: Record<number, string> = {
  0: $localize`:t1:Champion`,
  1: $localize`:t2:Finalist`,
  2: $localize`:t4:Semi-finals`,
  3: $localize`:t8:Quarter-finals`,
};

@Pipe({
  name: 'resultName'
})
export class ResultNamePipe implements PipeTransform {

  transform(value: number): unknown {
    return RESULTNAME_MAP[value];
  }
}
