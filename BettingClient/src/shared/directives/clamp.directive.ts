import { Directive, Input, HostListener, ElementRef } from '@angular/core';
import { NgControl } from '@angular/forms';

@Directive({
  selector: 'input[appClamp]',
  standalone: true
})
export class ClampDirective {
  @Input() minClamped: number = -Infinity;
  @Input() maxClamped: number = Infinity;

  constructor(private el: ElementRef, private control: NgControl) {}

  @HostListener('input', ['$event'])
  onInput(event: Event) {
    const inputElement = event.target as HTMLInputElement;
    const numValue = Number(inputElement.value);
    
    if (!isNaN(numValue)) {
      const clamped = Math.min(this.maxClamped, Math.max(this.minClamped, numValue));
      
      this.control.control?.setValue(clamped, { emitEvent: false });
      this.el.nativeElement.value = clamped;
    }
  }
}