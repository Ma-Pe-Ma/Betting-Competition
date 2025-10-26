import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DropdownSelector } from './dropdown-selector';

describe('DropdownSelector', () => {
  let component: DropdownSelector;
  let fixture: ComponentFixture<DropdownSelector>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DropdownSelector]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DropdownSelector);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
