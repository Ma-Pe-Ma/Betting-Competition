import { Component } from '@angular/core';
import { HttpDataHandler } from '../../../service/http-data-handler';
import { paths } from '../../../paths';

interface ResetKey {
  email: string
  date: string
  key: string
}

@Component({
  selector: 'app-password-reset',
  imports: [],
  templateUrl: './password-reset.html'
})
export class PasswordReset {
  resetKeys: ResetKey[] = []

  constructor(private httpDataHandler: HttpDataHandler) {
    let resetKeyPath = paths.admin.resetKeys;
    
    this.httpDataHandler.getData<ResetKey[]>(resetKeyPath).subscribe(value => {
      if (value && (value as any).message) {
      
      }
      else {
        this.resetKeys = value as ResetKey[];
      }
    });
  }
}


