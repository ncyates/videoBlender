import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class BlendService {
  encLink = ""
  constructor(private http: HttpClient) { }

  hitNodeAPI(link:string):Observable<any>{
    this.encLink = encodeURIComponent(link);
    console.log('The encoded link is ' + this.encLink);
    let url = 'vids/' + this.encLink;    
    return this.http.get(url,{responseType: 'text'});
  }
}
