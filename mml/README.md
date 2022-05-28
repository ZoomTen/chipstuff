# mml2pret

:yea:

## Compiler directives
<table>
   <thead>
      <tr>
         <th>Directive</th>
         <th>Description</th>
         <th>Example</th>
      </tr>
   </thead>
   <tbody>
      <tr>
         <td><code>#title</code></td>
         <td>
           <p>Name of the song to be output. This will be transformed into proper assembly labels.</p>
           <p>If omitted, the song will be called "Untitled".</p>
        </td>
        <td>
          <p><code>#title Home sweet home</code>.</p>
          <p>This will be compiled to: <code>Music_HomeSweetHome</code>.</p>
        </td>
      </tr>
      <tr>
         <td><code>#author</code></td>
         <td>Author of song. Completely optional.</td>
         <td><code>#author Zumi</code></td>
      </tr>
   </tbody>
</table>

## Commands
Note that all commands here are case INsensitive.
<table>
   <thead>
      <tr>
         <th>Command</th>
         <th>Description</th>
         <th>Example</th>
      </tr>
   </thead>
   <tbody>
      <tr>
        <td><code>t170</code></td>
         <td>
           <p>Sets the entire song's BPM to 170.</p>
        </td>
        <td>
          <ul>
            <li><code>t150</code></li>
            <li><code>t270</code></li>
            <li><code>t86</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c</code></td>
         <td>
           <p>Plays a C note in the standard length. This applies also to D, E, F, etc.</p>
        </td>
        <td>
          <ul>
            <li><code>c</code></li>
            <li><code>d</code></li>
            <li><code>cdefgab</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c+</code></td>
         <td>
           <p>Plays a C sharp note (C plus 1 semitone) in the standard length. This works for every note, e.g. `e+` will play an F note.</p>
        </td>
        <td>
          <ul>
            <li><code>c+</code></li>
            <li><code>a+</code></li>
            <li><code>d+d+e+f+</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c-</code></td>
         <td>
           <p>Plays a B note (C minus 1 semitone) in the standard length. This works for every note.</p>
        </td>
        <td>
          <ul>
            <li><code>c-</code></li>
            <li><code>f-</code></li>
            <li><code>c-b-a-g-</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c4</code></td>
         <td>
           <p>Plays a C note that's a 4th note.</p>
        </td>
        <td>
          <ul>
            <li><code>c4</code></li>
            <li><code>d4</code></li>
            <li><code>d4g4</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c-8</code></td>
         <td>
           <p>Plays a B note that's an 8th note.</p>
        </td>
        <td>
          <ul>
            <li><code>c-8d+16</code></li>
            <li><code>e+16e-32</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>c-8.</code></td>
         <td>
           <p>Plays a B note that's an 8th dotted note.</p>
        </td>
        <td>
          <ul>
            <li><code>c-8.c+4.</code></li>
            <li><code>e+8.e-8</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>l8</code></td>
         <td>
           <p>Sets the default length to an 8th note.</p>
        </td>
        <td>
          <ul>
            <li><code>l1</code></li>
            <li><code>l16</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>l8.</code></td>
         <td>
           <p>Sets the default length to an 8th dotted note.</p>
        </td>
        <td>
          <ul>
            <li><code>l1.</code></li>
            <li><code>l16.</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>o3</code></td>
         <td>
           <p>Sets the current octave to 3.</p>
        </td>
        <td>
          <ul>
            <li><code>o4</code></li>
            <li><code>o2</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>&gt;</code></td>
         <td>
           <p>Raises the octave.</p>
        </td>
        <td>
          <ul>
            <li><code>c d e &gt; e &gt; e</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>&lt;</code></td>
         <td>
           <p>Lowers the octave.</p>
        </td>
        <td>
          <ul>
            <li><code>c d e &lt; e &lt; e</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@duty(2)</code></td>
         <td>
           <p>Sets the duty cycle to 2 (50%).</p>
        </td>
        <td>
          <ul>
            <li><code>@duty(1)</code></li>
            <li><code>@duty(0)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@env(12 2)</code></td>
         <td>
           <p>Sets the GB envelope to start at volume 12 and fade by 2.</p>
        </td>
        <td>
          <ul>
            <li><code>@env(11 4)</code></li>
            <li><code>@env(4 -6)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@vib(9 3 4)</code></td>
         <td>
           <p>Sets the vibrato delay to 9, vib speed to 3 and extent to 4</p>
        </td>
        <td>
          <ul>
            <li><code>@vib(12 2 5)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@tone(2)</code></td>
         <td>
           <p>Sets the pitch offset to +2.</p>
        </td>
        <td>
          <ul>
            <li><code>@tone(2)</code></li>
            <li><code>@tone(3)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@drum(2)</code></td>
         <td>
           <p>Sets the 2nd drum set for use.</p>
        </td>
        <td>
          <ul>
            <li><code>@drum(1)</code></li>
            <li><code>@drum(0)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@vol(7 7)</code></td>
         <td>
           <p>Sets the Gameboy volume to $7 (left) and $7 (right).</p>
        </td>
        <td>
          <ul>
            <li><code>@vol(7 7)</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>@l</code></td>
         <td>
           <p>Sets the loop point of the track.</p>
        </td>
        <td>
          <ul>
            <li><code>@l</code></li>
          </ul>
        </td>
      </tr>
      <tr>
        <td><code>[c8d16e4]6</code></td>
         <td>
           <p>Loops the section "8th note C, 16th note D, 4th note E" 2 times.</p>
        </td>
        <td>
          <ul>
            <li><code>[defga+a+a-]4</code></li>
            <li><code>[gdc+c-a+]2</code></li>
          </ul>
        </td>
      </tr>
   </tbody>
</table>

File structure
```mml
#title Your title here
#author Your name here

/* You can have
   multiline comments anywhere in the file */

// as well as single line ones

/*
  Channel names are mapped to the gameboy
  
  A = channel 1
  B = channel 2
  C = channel 3
  D = channel 4
*/

/*
  MML data is enclosed in curly braces
*/
A { // first chanel
	t14 // tempo must be here!
	@tone(2) // pitch shift
@l
	cdefgab
  
  /* whitespace doesn't matter! */
}

B { // lead instrument
	l8 @duty(3)
	@vib(8 4 3)@
@l
  gabc
}

C { // bass
	@env(1 9) // wave instrument
@l
  a+a-c+
}
```
